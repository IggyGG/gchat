"""Fingerprint a worker's qualified implementation, not a mutable release label."""
import ast
import hashlib
import json
import os
from pathlib import Path
import re
import sys

from release_pair import canonical

ROOT = Path(__file__).resolve().parent
HELPER_MODULES = {'release_coordinator', 'release_control', 'release_ledger', 'release_failure', 'release_stores'}
MAXIMUM_SOURCE_BYTES = 2 * 1024 * 1024


def source_bytes(path):
    if path.is_symlink() or not path.is_file():
        raise ValueError('worker identity requires regular qualified source files')
    with path.open('rb') as stream:
        value = stream.read(MAXIMUM_SOURCE_BYTES + 1)
    if len(value) > MAXIMUM_SOURCE_BYTES:
        raise ValueError('worker identity source exceeds its bound')
    return value


def implementation(script, root=ROOT):
    """Conservative local import closure; control-plane helpers stay symbol-scoped.

    Otherwise importing atomic_json would make a status-only coordinator edit look
    like a change to every native/signing worker. Unknown imported helpers fail
    closed instead of acquiring a recipe-only identity.
    """
    root = Path(root).resolve()
    pending = [(script, None)]
    selected = {}
    inventory = {}
    while pending:
        name, symbols = pending.pop()
        if not re.fullmatch(r'[A-Za-z0-9_-]+', name):
            raise ValueError('invalid worker source module')
        if name in selected:
            previous = selected[name]
            if previous is None or symbols is not None and symbols <= previous:
                continue
            symbols = None if symbols is None else previous | symbols
        selected[name] = symbols
        if len(selected) > 160:
            raise ValueError('worker identity dependency graph exceeds its bound')
        path = root / (name + '.py')
        raw = source_bytes(path)
        tree = ast.parse(raw, filename=path.name)
        if symbols is None or name not in HELPER_MODULES:
            nodes = [tree]
            inventory[path.name] = hashlib.sha256(raw).hexdigest()
        else:
            definitions = {}
            for node in tree.body:
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    definitions[node.name] = node
                elif isinstance(node, (ast.Assign, ast.AnnAssign)):
                    targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                    for target in targets:
                        if isinstance(target, ast.Name): definitions[target.id] = node
            names = set(symbols)
            if not names <= definitions.keys():
                raise ValueError('worker imports an unrecognized control-plane helper')
            while True:
                referenced = {n.id for key in names for n in ast.walk(definitions[key])
                              if isinstance(n, ast.Name)} & definitions.keys()
                if referenced <= names: break
                names |= referenced
            nodes = [definitions[key] for key in sorted(names)]
            # Import spelling is part of identity, including module alias changes.
            imports = [node for node in tree.body if isinstance(node, (ast.Import, ast.ImportFrom))]
            inventory[path.name] = hashlib.sha256(canonical({
                'symbols': sorted(names), 'code': [ast.dump(n, include_attributes=False) for n in [*imports, *nodes]]
            })).hexdigest()
        used = {n.id for node in nodes for n in ast.walk(node) if isinstance(n, ast.Name)}
        imports = [n for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom))]
        for node in imports:
            if isinstance(node, ast.ImportFrom) and node.module and not node.level:
                module = node.module
                aliases = [a for a in node.names if symbols is None or (a.asname or a.name) in used]
                if aliases and (root / (module + '.py')).is_file():
                    names = {a.name for a in aliases}
                    pending.append((module, names if module in HELPER_MODULES and '*' not in names else None))
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if (symbols is None or (alias.asname or alias.name) in used) and (root / (alias.name + '.py')).is_file():
                        pending.append((alias.name, None))
        # Existing native validators load hyphenated helper names explicitly.
        for node in nodes:
            for call in ast.walk(node):
                if (isinstance(call, ast.Call) and isinstance(call.func, ast.Name)
                        and call.func.id in ('module', 'load_module') and call.args
                        and isinstance(call.args[0], ast.Constant) and isinstance(call.args[0].value, str)):
                    helper = call.args[0].value
                    if re.fullmatch(r'[A-Za-z0-9_-]+', helper) and (root / (helper + '.py')).is_file():
                        pending.append((helper, None))
    requirements = root.parent / 'release/automation/requirements.txt'
    if requirements.exists():
        inventory['release/automation/requirements.txt'] = hashlib.sha256(source_bytes(requirements)).hexdigest()
    return inventory


def cached_implementation(script, root, cache):
    def stamp(path):
        value = path.lstat()
        return (value.st_dev, value.st_ino, value.st_size, value.st_mtime_ns,
                value.st_ctime_ns, value.st_mode)
    key = (str(root), script)
    previous = cache.get(key) if cache is not None else None
    if previous is not None:
        try:
            if all(stamp(path) == value for path, value in previous['stamps'].items()):
                return previous['files']
        except FileNotFoundError:
            pass
    requirements = root.parent / 'release/automation/requirements.txt'
    before_paths = [root, *root.glob('*.py')]
    before_paths.append(requirements.parent if requirements.parent.exists() else root.parent)
    if requirements.exists(): before_paths.append(requirements)
    if len(before_paths) > 512:
        raise ValueError('worker source inventory exceeds its bound')
    before = {path: stamp(path) for path in before_paths}
    files = implementation(script, root)
    if cache is not None:
        paths = [root, *[root / name for name in files if '/' not in name]]
        paths += [root.parent / name for name in files if '/' in name]
        paths.append(requirements.parent if requirements.parent.exists() else root.parent)
        if any(before.get(path) != stamp(path) for path in paths):
            raise ValueError('qualified worker source changed during fingerprinting')
        cache[key] = {'files': files, 'stamps': {path: before[path] for path in paths}}
    return files


def fingerprint(recipe, platform, stage, *, root=ROOT, legacy_revision=None, cache=None):
    root = Path(root).resolve()
    argv = recipe.get('run', [])
    scripts = [Path(arg) for arg in argv if isinstance(arg, str) and arg.endswith('.py')]
    if not scripts:
        # Administrator-owned external recipes retain their explicit revision.
        return hashlib.sha256(canonical({'worker': recipe, 'controller': legacy_revision})).hexdigest()
    script = scripts[0]
    qualified = root / script.name
    if script.resolve() != qualified or not qualified.is_file():
        # An external Python recipe must declare a revision and binds its bytes.
        if not legacy_revision or not script.is_absolute():
            raise ValueError('worker recipe does not select a qualified script or explicit external revision')
        files = {script.name: hashlib.sha256(source_bytes(script)).hexdigest()}
    else:
        files = cached_implementation(script.stem, root, cache)
    configuration = {}
    for i, arg in enumerate(argv[:-1]):
        if arg != '--config': continue
        path = Path(argv[i + 1])
        if path.exists():
            # File references are hashed, not the credentials those references name.
            raw = source_bytes(path.resolve())
            if script.name == 'release_store_worker.py':
                settings = json.loads(raw)
                if isinstance(settings, dict):
                    # The other store's account settings are not this worker's
                    # correction. Unknown top-level settings stay conservative.
                    raw = canonical({k: v for k, v in settings.items() if k == platform or k not in ('android', 'ios')})
            configuration[str(path)] = hashlib.sha256(raw).hexdigest()
        else:
            configuration[str(path)] = 'missing'
    if 'release_macos_recovery.py' in files or 'release_ios_recovery.py' in files:
        path = Path(os.environ.get('GCHAT_NATIVE_RECOVERIES', str(root.parent / 'release/automation/qualification/native-recoveries.json')))
        configuration['native-recovery-registry'] = hashlib.sha256(source_bytes(path.resolve())).hexdigest() if path.exists() else 'missing'
    return hashlib.sha256(canonical({'schema': 2, 'platform': platform, 'stage': stage,
        'worker': recipe, 'python': list(sys.version_info[:3]), 'files': files,
        'configuration': configuration})).hexdigest()
