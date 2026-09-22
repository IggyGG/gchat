// @ts-nocheck
// Generated from Rust JSON schemas. Do not edit.
"use strict";
export const network_operation_args = validate20;
const schema31 = {"$defs":{"FileRequest":{"oneOf":[{"additionalProperties":false,"properties":{"action":{"const":"list","type":"string"},"conversation":{"type":["string","null"]}},"required":["action"],"type":"object"},{"additionalProperties":false,"properties":{"action":{"const":"prepare","type":"string"},"conversation":{"type":"string"},"id":{"type":"string"},"name":{"type":"string"},"size_bytes":{"type":"string"}},"required":["action","id","conversation","name","size_bytes"],"type":"object"},{"additionalProperties":false,"properties":{"action":{"const":"commit","type":"string"},"id":{"type":"string"}},"required":["action","id"],"type":"object"},{"additionalProperties":false,"properties":{"action":{"const":"accept","type":"string"},"id":{"type":"string"}},"required":["action","id"],"type":"object"},{"additionalProperties":false,"properties":{"action":{"const":"pause","type":"string"},"id":{"type":"string"}},"required":["action","id"],"type":"object"},{"additionalProperties":false,"properties":{"action":{"const":"resume","type":"string"},"id":{"type":"string"}},"required":["action","id"],"type":"object"},{"additionalProperties":false,"properties":{"action":{"const":"cancel","type":"string"},"id":{"type":"string"}},"required":["action","id"],"type":"object"},{"additionalProperties":false,"properties":{"action":{"const":"configure","type":"string"},"quota_bytes":{"type":"string"},"retention_days":{"format":"uint16","maximum":65535,"minimum":0,"type":"integer"}},"required":["action","quota_bytes","retention_days"],"type":"object"}]},"NetworkRequest":{"oneOf":[{"additionalProperties":false,"properties":{"kind":{"const":"list","type":"string"}},"required":["kind"],"type":"object"},{"additionalProperties":false,"properties":{"code":{"type":"string"},"kind":{"const":"inspect","type":"string"}},"required":["kind","code"],"type":"object"},{"additionalProperties":false,"properties":{"accepted_network":{"type":"string"},"code":{"type":"string"},"kind":{"const":"join","type":"string"},"nickname":{"type":"string"},"operation_id":{"type":"string"}},"required":["kind","code","nickname","accepted_network","operation_id"],"type":"object"},{"additionalProperties":false,"properties":{"kind":{"const":"call","type":"string"},"network":{"type":"string"},"request":{"$ref":"#/$defs/Request"}},"required":["kind","network","request"],"type":"object"}]},"Request":{"oneOf":[{"additionalProperties":false,"properties":{"kind":{"const":"networks","type":"string"},"request":{"$ref":"#/$defs/NetworkRequest"}},"required":["kind","request"],"type":"object"},{"additionalProperties":false,"properties":{"kind":{"const":"files","type":"string"},"request":{"$ref":"#/$defs/FileRequest"}},"required":["kind","request"],"type":"object"},{"additionalProperties":false,"properties":{"kind":{"const":"identify","type":"string"}},"required":["kind"],"type":"object"},{"additionalProperties":false,"properties":{"create":{"type":"boolean"},"kind":{"const":"unlock","type":"string"},"passphrase":{"type":"string"}},"required":["kind","passphrase","create"],"type":"object"},{"additionalProperties":false,"properties":{"kind":{"const":"lock","type":"string"}},"required":["kind"],"type":"object"},{"additionalProperties":false,"properties":{"kind":{"const":"disconnect","type":"string"}},"required":["kind"],"type":"object"},{"additionalProperties":false,"properties":{"kind":{"const":"snapshot","type":"string"}},"required":["kind"],"type":"object"},{"additionalProperties":false,"properties":{"kind":{"const":"network_status","type":"string"}},"required":["kind"],"type":"object"},{"additionalProperties":false,"properties":{"code":{"type":"string"},"kind":{"const":"import_network_invitation","type":"string"}},"required":["kind","code"],"type":"object"},{"additionalProperties":false,"properties":{"conversation":{"type":["string","null"]},"kind":{"const":"catalogue","type":"string"}},"required":["kind"],"type":"object"},{"additionalProperties":false,"properties":{"before":{"type":["string","null"]},"conversation":{"type":"string"},"kind":{"const":"history","type":"string"},"limit":{"format":"uint16","maximum":65535,"minimum":0,"type":"integer"}},"required":["kind","conversation","limit"],"type":"object"},{"additionalProperties":false,"properties":{"before":{"type":["string","null"]},"conversation":{"type":"string"},"kind":{"const":"search","type":"string"},"limit":{"format":"uint16","maximum":65535,"minimum":0,"type":"integer"},"text":{"type":"string"}},"required":["kind","conversation","text","limit"],"type":"object"},{"additionalProperties":false,"properties":{"conversation":{"type":["string","null"]},"kind":{"const":"submit","type":"string"},"operation_id":{"type":"string"},"text":{"type":"string"}},"required":["kind","operation_id","text"],"type":"object"},{"additionalProperties":false,"properties":{"conversation":{"type":["string","null"]},"kind":{"const":"complete","type":"string"},"text":{"type":"string"}},"required":["kind","text"],"type":"object"},{"additionalProperties":false,"properties":{"conversation":{"type":"string"},"kind":{"const":"mark_read","type":"string"},"message_id":{"type":"string"}},"required":["kind","conversation","message_id"],"type":"object"},{"additionalProperties":false,"properties":{"after":{"type":"string"},"kind":{"const":"events","type":"string"},"wait_ms":{"format":"uint16","maximum":65535,"minimum":0,"type":"integer"}},"required":["kind","after","wait_ms"],"type":"object"}]}},"$schema":"https://json-schema.org/draft/2020-12/schema","additionalProperties":false,"properties":{"request":{"$ref":"#/$defs/NetworkRequest"}},"required":["request"],"title":"ChatNetworkOperationArgs","type":"object"};
const schema32 = {"oneOf":[{"additionalProperties":false,"properties":{"kind":{"const":"list","type":"string"}},"required":["kind"],"type":"object"},{"additionalProperties":false,"properties":{"code":{"type":"string"},"kind":{"const":"inspect","type":"string"}},"required":["kind","code"],"type":"object"},{"additionalProperties":false,"properties":{"accepted_network":{"type":"string"},"code":{"type":"string"},"kind":{"const":"join","type":"string"},"nickname":{"type":"string"},"operation_id":{"type":"string"}},"required":["kind","code","nickname","accepted_network","operation_id"],"type":"object"},{"additionalProperties":false,"properties":{"kind":{"const":"call","type":"string"},"network":{"type":"string"},"request":{"$ref":"#/$defs/Request"}},"required":["kind","network","request"],"type":"object"}]};
const schema33 = {"oneOf":[{"additionalProperties":false,"properties":{"kind":{"const":"networks","type":"string"},"request":{"$ref":"#/$defs/NetworkRequest"}},"required":["kind","request"],"type":"object"},{"additionalProperties":false,"properties":{"kind":{"const":"files","type":"string"},"request":{"$ref":"#/$defs/FileRequest"}},"required":["kind","request"],"type":"object"},{"additionalProperties":false,"properties":{"kind":{"const":"identify","type":"string"}},"required":["kind"],"type":"object"},{"additionalProperties":false,"properties":{"create":{"type":"boolean"},"kind":{"const":"unlock","type":"string"},"passphrase":{"type":"string"}},"required":["kind","passphrase","create"],"type":"object"},{"additionalProperties":false,"properties":{"kind":{"const":"lock","type":"string"}},"required":["kind"],"type":"object"},{"additionalProperties":false,"properties":{"kind":{"const":"disconnect","type":"string"}},"required":["kind"],"type":"object"},{"additionalProperties":false,"properties":{"kind":{"const":"snapshot","type":"string"}},"required":["kind"],"type":"object"},{"additionalProperties":false,"properties":{"kind":{"const":"network_status","type":"string"}},"required":["kind"],"type":"object"},{"additionalProperties":false,"properties":{"code":{"type":"string"},"kind":{"const":"import_network_invitation","type":"string"}},"required":["kind","code"],"type":"object"},{"additionalProperties":false,"properties":{"conversation":{"type":["string","null"]},"kind":{"const":"catalogue","type":"string"}},"required":["kind"],"type":"object"},{"additionalProperties":false,"properties":{"before":{"type":["string","null"]},"conversation":{"type":"string"},"kind":{"const":"history","type":"string"},"limit":{"format":"uint16","maximum":65535,"minimum":0,"type":"integer"}},"required":["kind","conversation","limit"],"type":"object"},{"additionalProperties":false,"properties":{"before":{"type":["string","null"]},"conversation":{"type":"string"},"kind":{"const":"search","type":"string"},"limit":{"format":"uint16","maximum":65535,"minimum":0,"type":"integer"},"text":{"type":"string"}},"required":["kind","conversation","text","limit"],"type":"object"},{"additionalProperties":false,"properties":{"conversation":{"type":["string","null"]},"kind":{"const":"submit","type":"string"},"operation_id":{"type":"string"},"text":{"type":"string"}},"required":["kind","operation_id","text"],"type":"object"},{"additionalProperties":false,"properties":{"conversation":{"type":["string","null"]},"kind":{"const":"complete","type":"string"},"text":{"type":"string"}},"required":["kind","text"],"type":"object"},{"additionalProperties":false,"properties":{"conversation":{"type":"string"},"kind":{"const":"mark_read","type":"string"},"message_id":{"type":"string"}},"required":["kind","conversation","message_id"],"type":"object"},{"additionalProperties":false,"properties":{"after":{"type":"string"},"kind":{"const":"events","type":"string"},"wait_ms":{"format":"uint16","maximum":65535,"minimum":0,"type":"integer"}},"required":["kind","after","wait_ms"],"type":"object"}]};
const schema34 = {"oneOf":[{"additionalProperties":false,"properties":{"action":{"const":"list","type":"string"},"conversation":{"type":["string","null"]}},"required":["action"],"type":"object"},{"additionalProperties":false,"properties":{"action":{"const":"prepare","type":"string"},"conversation":{"type":"string"},"id":{"type":"string"},"name":{"type":"string"},"size_bytes":{"type":"string"}},"required":["action","id","conversation","name","size_bytes"],"type":"object"},{"additionalProperties":false,"properties":{"action":{"const":"commit","type":"string"},"id":{"type":"string"}},"required":["action","id"],"type":"object"},{"additionalProperties":false,"properties":{"action":{"const":"accept","type":"string"},"id":{"type":"string"}},"required":["action","id"],"type":"object"},{"additionalProperties":false,"properties":{"action":{"const":"pause","type":"string"},"id":{"type":"string"}},"required":["action","id"],"type":"object"},{"additionalProperties":false,"properties":{"action":{"const":"resume","type":"string"},"id":{"type":"string"}},"required":["action","id"],"type":"object"},{"additionalProperties":false,"properties":{"action":{"const":"cancel","type":"string"},"id":{"type":"string"}},"required":["action","id"],"type":"object"},{"additionalProperties":false,"properties":{"action":{"const":"configure","type":"string"},"quota_bytes":{"type":"string"},"retention_days":{"format":"uint16","maximum":65535,"minimum":0,"type":"integer"}},"required":["action","quota_bytes","retention_days"],"type":"object"}]};
const wrapper0 = {validate: validate21};

function validate22(data, {instancePath="", parentData, parentDataProperty, rootData=data, dynamicAnchors={}}={}){
let vErrors = null;
let errors = 0;
const evaluated0 = validate22.evaluated;
if(evaluated0.dynamicProps){
evaluated0.props = undefined;
}
if(evaluated0.dynamicItems){
evaluated0.items = undefined;
}
const _errs0 = errors;
let valid0 = false;
let passing0 = null;
const _errs1 = errors;
if(errors === _errs1){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing0;
if(((data.kind === undefined) && (missing0 = "kind")) || ((data.request === undefined) && (missing0 = "request"))){
const err0 = {instancePath,schemaPath:"#/oneOf/0/required",keyword:"required",params:{missingProperty: missing0},message:"must have required property '"+missing0+"'"};
if(vErrors === null){
vErrors = [err0];
}
else {
vErrors.push(err0);
}
errors++;
}
else {
const _errs3 = errors;
for(const key0 in data){
if(!((key0 === "kind") || (key0 === "request"))){
const err1 = {instancePath,schemaPath:"#/oneOf/0/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key0},message:"must NOT have additional properties"};
if(vErrors === null){
vErrors = [err1];
}
else {
vErrors.push(err1);
}
errors++;
break;
}
}
if(_errs3 === errors){
if(data.kind !== undefined){
let data0 = data.kind;
const _errs4 = errors;
if(typeof data0 !== "string"){
const err2 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/0/properties/kind/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err2];
}
else {
vErrors.push(err2);
}
errors++;
}
if("networks" !== data0){
const err3 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/0/properties/kind/const",keyword:"const",params:{allowedValue: "networks"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err3];
}
else {
vErrors.push(err3);
}
errors++;
}
var valid1 = _errs4 === errors;
}
else {
var valid1 = true;
}
if(valid1){
if(data.request !== undefined){
const _errs6 = errors;
if(!(wrapper0.validate(data.request, {instancePath:instancePath+"/request",parentData:data,parentDataProperty:"request",rootData,dynamicAnchors}))){
vErrors = vErrors === null ? wrapper0.validate.errors : vErrors.concat(wrapper0.validate.errors);
errors = vErrors.length;
}
var valid1 = _errs6 === errors;
}
else {
var valid1 = true;
}
}
}
}
}
else {
const err4 = {instancePath,schemaPath:"#/oneOf/0/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err4];
}
else {
vErrors.push(err4);
}
errors++;
}
}
var _valid0 = _errs1 === errors;
if(_valid0){
valid0 = true;
passing0 = 0;
var props1 = true;
}
const _errs7 = errors;
if(errors === _errs7){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing1;
if(((data.kind === undefined) && (missing1 = "kind")) || ((data.request === undefined) && (missing1 = "request"))){
const err5 = {instancePath,schemaPath:"#/oneOf/1/required",keyword:"required",params:{missingProperty: missing1},message:"must have required property '"+missing1+"'"};
if(vErrors === null){
vErrors = [err5];
}
else {
vErrors.push(err5);
}
errors++;
}
else {
const _errs9 = errors;
for(const key1 in data){
if(!((key1 === "kind") || (key1 === "request"))){
const err6 = {instancePath,schemaPath:"#/oneOf/1/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key1},message:"must NOT have additional properties"};
if(vErrors === null){
vErrors = [err6];
}
else {
vErrors.push(err6);
}
errors++;
break;
}
}
if(_errs9 === errors){
if(data.kind !== undefined){
let data2 = data.kind;
const _errs10 = errors;
if(typeof data2 !== "string"){
const err7 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/1/properties/kind/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err7];
}
else {
vErrors.push(err7);
}
errors++;
}
if("files" !== data2){
const err8 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/1/properties/kind/const",keyword:"const",params:{allowedValue: "files"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err8];
}
else {
vErrors.push(err8);
}
errors++;
}
var valid2 = _errs10 === errors;
}
else {
var valid2 = true;
}
if(valid2){
if(data.request !== undefined){
let data3 = data.request;
const _errs12 = errors;
const _errs14 = errors;
let valid4 = false;
let passing1 = null;
const _errs15 = errors;
if(errors === _errs15){
if(data3 && typeof data3 == "object" && !Array.isArray(data3)){
let missing2;
if((data3.action === undefined) && (missing2 = "action")){
const err9 = {instancePath:instancePath+"/request",schemaPath:"#/$defs/FileRequest/oneOf/0/required",keyword:"required",params:{missingProperty: missing2},message:"must have required property '"+missing2+"'"};
if(vErrors === null){
vErrors = [err9];
}
else {
vErrors.push(err9);
}
errors++;
}
else {
const _errs17 = errors;
for(const key2 in data3){
if(!((key2 === "action") || (key2 === "conversation"))){
const err10 = {instancePath:instancePath+"/request",schemaPath:"#/$defs/FileRequest/oneOf/0/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key2},message:"must NOT have additional properties"};
if(vErrors === null){
vErrors = [err10];
}
else {
vErrors.push(err10);
}
errors++;
break;
}
}
if(_errs17 === errors){
if(data3.action !== undefined){
let data4 = data3.action;
const _errs18 = errors;
if(typeof data4 !== "string"){
const err11 = {instancePath:instancePath+"/request/action",schemaPath:"#/$defs/FileRequest/oneOf/0/properties/action/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err11];
}
else {
vErrors.push(err11);
}
errors++;
}
if("list" !== data4){
const err12 = {instancePath:instancePath+"/request/action",schemaPath:"#/$defs/FileRequest/oneOf/0/properties/action/const",keyword:"const",params:{allowedValue: "list"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err12];
}
else {
vErrors.push(err12);
}
errors++;
}
var valid5 = _errs18 === errors;
}
else {
var valid5 = true;
}
if(valid5){
if(data3.conversation !== undefined){
let data5 = data3.conversation;
const _errs20 = errors;
if((typeof data5 !== "string") && (data5 !== null)){
const err13 = {instancePath:instancePath+"/request/conversation",schemaPath:"#/$defs/FileRequest/oneOf/0/properties/conversation/type",keyword:"type",params:{type: schema34.oneOf[0].properties.conversation.type},message:"must be string,null"};
if(vErrors === null){
vErrors = [err13];
}
else {
vErrors.push(err13);
}
errors++;
}
var valid5 = _errs20 === errors;
}
else {
var valid5 = true;
}
}
}
}
}
else {
const err14 = {instancePath:instancePath+"/request",schemaPath:"#/$defs/FileRequest/oneOf/0/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err14];
}
else {
vErrors.push(err14);
}
errors++;
}
}
var _valid1 = _errs15 === errors;
if(_valid1){
valid4 = true;
passing1 = 0;
var props2 = true;
}
const _errs22 = errors;
if(errors === _errs22){
if(data3 && typeof data3 == "object" && !Array.isArray(data3)){
let missing3;
if((((((data3.action === undefined) && (missing3 = "action")) || ((data3.id === undefined) && (missing3 = "id"))) || ((data3.conversation === undefined) && (missing3 = "conversation"))) || ((data3.name === undefined) && (missing3 = "name"))) || ((data3.size_bytes === undefined) && (missing3 = "size_bytes"))){
const err15 = {instancePath:instancePath+"/request",schemaPath:"#/$defs/FileRequest/oneOf/1/required",keyword:"required",params:{missingProperty: missing3},message:"must have required property '"+missing3+"'"};
if(vErrors === null){
vErrors = [err15];
}
else {
vErrors.push(err15);
}
errors++;
}
else {
const _errs24 = errors;
for(const key3 in data3){
if(!(((((key3 === "action") || (key3 === "conversation")) || (key3 === "id")) || (key3 === "name")) || (key3 === "size_bytes"))){
const err16 = {instancePath:instancePath+"/request",schemaPath:"#/$defs/FileRequest/oneOf/1/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key3},message:"must NOT have additional properties"};
if(vErrors === null){
vErrors = [err16];
}
else {
vErrors.push(err16);
}
errors++;
break;
}
}
if(_errs24 === errors){
if(data3.action !== undefined){
let data6 = data3.action;
const _errs25 = errors;
if(typeof data6 !== "string"){
const err17 = {instancePath:instancePath+"/request/action",schemaPath:"#/$defs/FileRequest/oneOf/1/properties/action/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err17];
}
else {
vErrors.push(err17);
}
errors++;
}
if("prepare" !== data6){
const err18 = {instancePath:instancePath+"/request/action",schemaPath:"#/$defs/FileRequest/oneOf/1/properties/action/const",keyword:"const",params:{allowedValue: "prepare"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err18];
}
else {
vErrors.push(err18);
}
errors++;
}
var valid6 = _errs25 === errors;
}
else {
var valid6 = true;
}
if(valid6){
if(data3.conversation !== undefined){
const _errs27 = errors;
if(typeof data3.conversation !== "string"){
const err19 = {instancePath:instancePath+"/request/conversation",schemaPath:"#/$defs/FileRequest/oneOf/1/properties/conversation/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err19];
}
else {
vErrors.push(err19);
}
errors++;
}
var valid6 = _errs27 === errors;
}
else {
var valid6 = true;
}
if(valid6){
if(data3.id !== undefined){
const _errs29 = errors;
if(typeof data3.id !== "string"){
const err20 = {instancePath:instancePath+"/request/id",schemaPath:"#/$defs/FileRequest/oneOf/1/properties/id/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err20];
}
else {
vErrors.push(err20);
}
errors++;
}
var valid6 = _errs29 === errors;
}
else {
var valid6 = true;
}
if(valid6){
if(data3.name !== undefined){
const _errs31 = errors;
if(typeof data3.name !== "string"){
const err21 = {instancePath:instancePath+"/request/name",schemaPath:"#/$defs/FileRequest/oneOf/1/properties/name/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err21];
}
else {
vErrors.push(err21);
}
errors++;
}
var valid6 = _errs31 === errors;
}
else {
var valid6 = true;
}
if(valid6){
if(data3.size_bytes !== undefined){
const _errs33 = errors;
if(typeof data3.size_bytes !== "string"){
const err22 = {instancePath:instancePath+"/request/size_bytes",schemaPath:"#/$defs/FileRequest/oneOf/1/properties/size_bytes/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err22];
}
else {
vErrors.push(err22);
}
errors++;
}
var valid6 = _errs33 === errors;
}
else {
var valid6 = true;
}
}
}
}
}
}
}
}
else {
const err23 = {instancePath:instancePath+"/request",schemaPath:"#/$defs/FileRequest/oneOf/1/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err23];
}
else {
vErrors.push(err23);
}
errors++;
}
}
var _valid1 = _errs22 === errors;
if(_valid1 && valid4){
valid4 = false;
passing1 = [passing1, 1];
}
else {
if(_valid1){
valid4 = true;
passing1 = 1;
if(props2 !== true){
props2 = true;
}
}
const _errs35 = errors;
if(errors === _errs35){
if(data3 && typeof data3 == "object" && !Array.isArray(data3)){
let missing4;
if(((data3.action === undefined) && (missing4 = "action")) || ((data3.id === undefined) && (missing4 = "id"))){
const err24 = {instancePath:instancePath+"/request",schemaPath:"#/$defs/FileRequest/oneOf/2/required",keyword:"required",params:{missingProperty: missing4},message:"must have required property '"+missing4+"'"};
if(vErrors === null){
vErrors = [err24];
}
else {
vErrors.push(err24);
}
errors++;
}
else {
const _errs37 = errors;
for(const key4 in data3){
if(!((key4 === "action") || (key4 === "id"))){
const err25 = {instancePath:instancePath+"/request",schemaPath:"#/$defs/FileRequest/oneOf/2/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key4},message:"must NOT have additional properties"};
if(vErrors === null){
vErrors = [err25];
}
else {
vErrors.push(err25);
}
errors++;
break;
}
}
if(_errs37 === errors){
if(data3.action !== undefined){
let data11 = data3.action;
const _errs38 = errors;
if(typeof data11 !== "string"){
const err26 = {instancePath:instancePath+"/request/action",schemaPath:"#/$defs/FileRequest/oneOf/2/properties/action/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err26];
}
else {
vErrors.push(err26);
}
errors++;
}
if("commit" !== data11){
const err27 = {instancePath:instancePath+"/request/action",schemaPath:"#/$defs/FileRequest/oneOf/2/properties/action/const",keyword:"const",params:{allowedValue: "commit"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err27];
}
else {
vErrors.push(err27);
}
errors++;
}
var valid7 = _errs38 === errors;
}
else {
var valid7 = true;
}
if(valid7){
if(data3.id !== undefined){
const _errs40 = errors;
if(typeof data3.id !== "string"){
const err28 = {instancePath:instancePath+"/request/id",schemaPath:"#/$defs/FileRequest/oneOf/2/properties/id/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err28];
}
else {
vErrors.push(err28);
}
errors++;
}
var valid7 = _errs40 === errors;
}
else {
var valid7 = true;
}
}
}
}
}
else {
const err29 = {instancePath:instancePath+"/request",schemaPath:"#/$defs/FileRequest/oneOf/2/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err29];
}
else {
vErrors.push(err29);
}
errors++;
}
}
var _valid1 = _errs35 === errors;
if(_valid1 && valid4){
valid4 = false;
passing1 = [passing1, 2];
}
else {
if(_valid1){
valid4 = true;
passing1 = 2;
if(props2 !== true){
props2 = true;
}
}
const _errs42 = errors;
if(errors === _errs42){
if(data3 && typeof data3 == "object" && !Array.isArray(data3)){
let missing5;
if(((data3.action === undefined) && (missing5 = "action")) || ((data3.id === undefined) && (missing5 = "id"))){
const err30 = {instancePath:instancePath+"/request",schemaPath:"#/$defs/FileRequest/oneOf/3/required",keyword:"required",params:{missingProperty: missing5},message:"must have required property '"+missing5+"'"};
if(vErrors === null){
vErrors = [err30];
}
else {
vErrors.push(err30);
}
errors++;
}
else {
const _errs44 = errors;
for(const key5 in data3){
if(!((key5 === "action") || (key5 === "id"))){
const err31 = {instancePath:instancePath+"/request",schemaPath:"#/$defs/FileRequest/oneOf/3/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key5},message:"must NOT have additional properties"};
if(vErrors === null){
vErrors = [err31];
}
else {
vErrors.push(err31);
}
errors++;
break;
}
}
if(_errs44 === errors){
if(data3.action !== undefined){
let data13 = data3.action;
const _errs45 = errors;
if(typeof data13 !== "string"){
const err32 = {instancePath:instancePath+"/request/action",schemaPath:"#/$defs/FileRequest/oneOf/3/properties/action/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err32];
}
else {
vErrors.push(err32);
}
errors++;
}
if("accept" !== data13){
const err33 = {instancePath:instancePath+"/request/action",schemaPath:"#/$defs/FileRequest/oneOf/3/properties/action/const",keyword:"const",params:{allowedValue: "accept"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err33];
}
else {
vErrors.push(err33);
}
errors++;
}
var valid8 = _errs45 === errors;
}
else {
var valid8 = true;
}
if(valid8){
if(data3.id !== undefined){
const _errs47 = errors;
if(typeof data3.id !== "string"){
const err34 = {instancePath:instancePath+"/request/id",schemaPath:"#/$defs/FileRequest/oneOf/3/properties/id/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err34];
}
else {
vErrors.push(err34);
}
errors++;
}
var valid8 = _errs47 === errors;
}
else {
var valid8 = true;
}
}
}
}
}
else {
const err35 = {instancePath:instancePath+"/request",schemaPath:"#/$defs/FileRequest/oneOf/3/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err35];
}
else {
vErrors.push(err35);
}
errors++;
}
}
var _valid1 = _errs42 === errors;
if(_valid1 && valid4){
valid4 = false;
passing1 = [passing1, 3];
}
else {
if(_valid1){
valid4 = true;
passing1 = 3;
if(props2 !== true){
props2 = true;
}
}
const _errs49 = errors;
if(errors === _errs49){
if(data3 && typeof data3 == "object" && !Array.isArray(data3)){
let missing6;
if(((data3.action === undefined) && (missing6 = "action")) || ((data3.id === undefined) && (missing6 = "id"))){
const err36 = {instancePath:instancePath+"/request",schemaPath:"#/$defs/FileRequest/oneOf/4/required",keyword:"required",params:{missingProperty: missing6},message:"must have required property '"+missing6+"'"};
if(vErrors === null){
vErrors = [err36];
}
else {
vErrors.push(err36);
}
errors++;
}
else {
const _errs51 = errors;
for(const key6 in data3){
if(!((key6 === "action") || (key6 === "id"))){
const err37 = {instancePath:instancePath+"/request",schemaPath:"#/$defs/FileRequest/oneOf/4/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key6},message:"must NOT have additional properties"};
if(vErrors === null){
vErrors = [err37];
}
else {
vErrors.push(err37);
}
errors++;
break;
}
}
if(_errs51 === errors){
if(data3.action !== undefined){
let data15 = data3.action;
const _errs52 = errors;
if(typeof data15 !== "string"){
const err38 = {instancePath:instancePath+"/request/action",schemaPath:"#/$defs/FileRequest/oneOf/4/properties/action/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err38];
}
else {
vErrors.push(err38);
}
errors++;
}
if("pause" !== data15){
const err39 = {instancePath:instancePath+"/request/action",schemaPath:"#/$defs/FileRequest/oneOf/4/properties/action/const",keyword:"const",params:{allowedValue: "pause"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err39];
}
else {
vErrors.push(err39);
}
errors++;
}
var valid9 = _errs52 === errors;
}
else {
var valid9 = true;
}
if(valid9){
if(data3.id !== undefined){
const _errs54 = errors;
if(typeof data3.id !== "string"){
const err40 = {instancePath:instancePath+"/request/id",schemaPath:"#/$defs/FileRequest/oneOf/4/properties/id/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err40];
}
else {
vErrors.push(err40);
}
errors++;
}
var valid9 = _errs54 === errors;
}
else {
var valid9 = true;
}
}
}
}
}
else {
const err41 = {instancePath:instancePath+"/request",schemaPath:"#/$defs/FileRequest/oneOf/4/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err41];
}
else {
vErrors.push(err41);
}
errors++;
}
}
var _valid1 = _errs49 === errors;
if(_valid1 && valid4){
valid4 = false;
passing1 = [passing1, 4];
}
else {
if(_valid1){
valid4 = true;
passing1 = 4;
if(props2 !== true){
props2 = true;
}
}
const _errs56 = errors;
if(errors === _errs56){
if(data3 && typeof data3 == "object" && !Array.isArray(data3)){
let missing7;
if(((data3.action === undefined) && (missing7 = "action")) || ((data3.id === undefined) && (missing7 = "id"))){
const err42 = {instancePath:instancePath+"/request",schemaPath:"#/$defs/FileRequest/oneOf/5/required",keyword:"required",params:{missingProperty: missing7},message:"must have required property '"+missing7+"'"};
if(vErrors === null){
vErrors = [err42];
}
else {
vErrors.push(err42);
}
errors++;
}
else {
const _errs58 = errors;
for(const key7 in data3){
if(!((key7 === "action") || (key7 === "id"))){
const err43 = {instancePath:instancePath+"/request",schemaPath:"#/$defs/FileRequest/oneOf/5/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key7},message:"must NOT have additional properties"};
if(vErrors === null){
vErrors = [err43];
}
else {
vErrors.push(err43);
}
errors++;
break;
}
}
if(_errs58 === errors){
if(data3.action !== undefined){
let data17 = data3.action;
const _errs59 = errors;
if(typeof data17 !== "string"){
const err44 = {instancePath:instancePath+"/request/action",schemaPath:"#/$defs/FileRequest/oneOf/5/properties/action/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err44];
}
else {
vErrors.push(err44);
}
errors++;
}
if("resume" !== data17){
const err45 = {instancePath:instancePath+"/request/action",schemaPath:"#/$defs/FileRequest/oneOf/5/properties/action/const",keyword:"const",params:{allowedValue: "resume"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err45];
}
else {
vErrors.push(err45);
}
errors++;
}
var valid10 = _errs59 === errors;
}
else {
var valid10 = true;
}
if(valid10){
if(data3.id !== undefined){
const _errs61 = errors;
if(typeof data3.id !== "string"){
const err46 = {instancePath:instancePath+"/request/id",schemaPath:"#/$defs/FileRequest/oneOf/5/properties/id/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err46];
}
else {
vErrors.push(err46);
}
errors++;
}
var valid10 = _errs61 === errors;
}
else {
var valid10 = true;
}
}
}
}
}
else {
const err47 = {instancePath:instancePath+"/request",schemaPath:"#/$defs/FileRequest/oneOf/5/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err47];
}
else {
vErrors.push(err47);
}
errors++;
}
}
var _valid1 = _errs56 === errors;
if(_valid1 && valid4){
valid4 = false;
passing1 = [passing1, 5];
}
else {
if(_valid1){
valid4 = true;
passing1 = 5;
if(props2 !== true){
props2 = true;
}
}
const _errs63 = errors;
if(errors === _errs63){
if(data3 && typeof data3 == "object" && !Array.isArray(data3)){
let missing8;
if(((data3.action === undefined) && (missing8 = "action")) || ((data3.id === undefined) && (missing8 = "id"))){
const err48 = {instancePath:instancePath+"/request",schemaPath:"#/$defs/FileRequest/oneOf/6/required",keyword:"required",params:{missingProperty: missing8},message:"must have required property '"+missing8+"'"};
if(vErrors === null){
vErrors = [err48];
}
else {
vErrors.push(err48);
}
errors++;
}
else {
const _errs65 = errors;
for(const key8 in data3){
if(!((key8 === "action") || (key8 === "id"))){
const err49 = {instancePath:instancePath+"/request",schemaPath:"#/$defs/FileRequest/oneOf/6/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key8},message:"must NOT have additional properties"};
if(vErrors === null){
vErrors = [err49];
}
else {
vErrors.push(err49);
}
errors++;
break;
}
}
if(_errs65 === errors){
if(data3.action !== undefined){
let data19 = data3.action;
const _errs66 = errors;
if(typeof data19 !== "string"){
const err50 = {instancePath:instancePath+"/request/action",schemaPath:"#/$defs/FileRequest/oneOf/6/properties/action/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err50];
}
else {
vErrors.push(err50);
}
errors++;
}
if("cancel" !== data19){
const err51 = {instancePath:instancePath+"/request/action",schemaPath:"#/$defs/FileRequest/oneOf/6/properties/action/const",keyword:"const",params:{allowedValue: "cancel"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err51];
}
else {
vErrors.push(err51);
}
errors++;
}
var valid11 = _errs66 === errors;
}
else {
var valid11 = true;
}
if(valid11){
if(data3.id !== undefined){
const _errs68 = errors;
if(typeof data3.id !== "string"){
const err52 = {instancePath:instancePath+"/request/id",schemaPath:"#/$defs/FileRequest/oneOf/6/properties/id/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err52];
}
else {
vErrors.push(err52);
}
errors++;
}
var valid11 = _errs68 === errors;
}
else {
var valid11 = true;
}
}
}
}
}
else {
const err53 = {instancePath:instancePath+"/request",schemaPath:"#/$defs/FileRequest/oneOf/6/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err53];
}
else {
vErrors.push(err53);
}
errors++;
}
}
var _valid1 = _errs63 === errors;
if(_valid1 && valid4){
valid4 = false;
passing1 = [passing1, 6];
}
else {
if(_valid1){
valid4 = true;
passing1 = 6;
if(props2 !== true){
props2 = true;
}
}
const _errs70 = errors;
if(errors === _errs70){
if(data3 && typeof data3 == "object" && !Array.isArray(data3)){
let missing9;
if((((data3.action === undefined) && (missing9 = "action")) || ((data3.quota_bytes === undefined) && (missing9 = "quota_bytes"))) || ((data3.retention_days === undefined) && (missing9 = "retention_days"))){
const err54 = {instancePath:instancePath+"/request",schemaPath:"#/$defs/FileRequest/oneOf/7/required",keyword:"required",params:{missingProperty: missing9},message:"must have required property '"+missing9+"'"};
if(vErrors === null){
vErrors = [err54];
}
else {
vErrors.push(err54);
}
errors++;
}
else {
const _errs72 = errors;
for(const key9 in data3){
if(!(((key9 === "action") || (key9 === "quota_bytes")) || (key9 === "retention_days"))){
const err55 = {instancePath:instancePath+"/request",schemaPath:"#/$defs/FileRequest/oneOf/7/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key9},message:"must NOT have additional properties"};
if(vErrors === null){
vErrors = [err55];
}
else {
vErrors.push(err55);
}
errors++;
break;
}
}
if(_errs72 === errors){
if(data3.action !== undefined){
let data21 = data3.action;
const _errs73 = errors;
if(typeof data21 !== "string"){
const err56 = {instancePath:instancePath+"/request/action",schemaPath:"#/$defs/FileRequest/oneOf/7/properties/action/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err56];
}
else {
vErrors.push(err56);
}
errors++;
}
if("configure" !== data21){
const err57 = {instancePath:instancePath+"/request/action",schemaPath:"#/$defs/FileRequest/oneOf/7/properties/action/const",keyword:"const",params:{allowedValue: "configure"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err57];
}
else {
vErrors.push(err57);
}
errors++;
}
var valid12 = _errs73 === errors;
}
else {
var valid12 = true;
}
if(valid12){
if(data3.quota_bytes !== undefined){
const _errs75 = errors;
if(typeof data3.quota_bytes !== "string"){
const err58 = {instancePath:instancePath+"/request/quota_bytes",schemaPath:"#/$defs/FileRequest/oneOf/7/properties/quota_bytes/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err58];
}
else {
vErrors.push(err58);
}
errors++;
}
var valid12 = _errs75 === errors;
}
else {
var valid12 = true;
}
if(valid12){
if(data3.retention_days !== undefined){
let data23 = data3.retention_days;
const _errs77 = errors;
if(!(((typeof data23 == "number") && (!(data23 % 1) && !isNaN(data23))) && (isFinite(data23)))){
const err59 = {instancePath:instancePath+"/request/retention_days",schemaPath:"#/$defs/FileRequest/oneOf/7/properties/retention_days/type",keyword:"type",params:{type: "integer"},message:"must be integer"};
if(vErrors === null){
vErrors = [err59];
}
else {
vErrors.push(err59);
}
errors++;
}
if(errors === _errs77){
if((typeof data23 == "number") && (isFinite(data23))){
if(data23 > 65535 || isNaN(data23)){
const err60 = {instancePath:instancePath+"/request/retention_days",schemaPath:"#/$defs/FileRequest/oneOf/7/properties/retention_days/maximum",keyword:"maximum",params:{comparison: "<=", limit: 65535},message:"must be <= 65535"};
if(vErrors === null){
vErrors = [err60];
}
else {
vErrors.push(err60);
}
errors++;
}
else {
if(data23 < 0 || isNaN(data23)){
const err61 = {instancePath:instancePath+"/request/retention_days",schemaPath:"#/$defs/FileRequest/oneOf/7/properties/retention_days/minimum",keyword:"minimum",params:{comparison: ">=", limit: 0},message:"must be >= 0"};
if(vErrors === null){
vErrors = [err61];
}
else {
vErrors.push(err61);
}
errors++;
}
}
}
}
var valid12 = _errs77 === errors;
}
else {
var valid12 = true;
}
}
}
}
}
}
else {
const err62 = {instancePath:instancePath+"/request",schemaPath:"#/$defs/FileRequest/oneOf/7/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err62];
}
else {
vErrors.push(err62);
}
errors++;
}
}
var _valid1 = _errs70 === errors;
if(_valid1 && valid4){
valid4 = false;
passing1 = [passing1, 7];
}
else {
if(_valid1){
valid4 = true;
passing1 = 7;
if(props2 !== true){
props2 = true;
}
}
}
}
}
}
}
}
}
if(!valid4){
const err63 = {instancePath:instancePath+"/request",schemaPath:"#/$defs/FileRequest/oneOf",keyword:"oneOf",params:{passingSchemas: passing1},message:"must match exactly one schema in oneOf"};
if(vErrors === null){
vErrors = [err63];
}
else {
vErrors.push(err63);
}
errors++;
}
else {
errors = _errs14;
if(vErrors !== null){
if(_errs14){
vErrors.length = _errs14;
}
else {
vErrors = null;
}
}
}
var valid2 = _errs12 === errors;
}
else {
var valid2 = true;
}
}
}
}
}
else {
const err64 = {instancePath,schemaPath:"#/oneOf/1/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err64];
}
else {
vErrors.push(err64);
}
errors++;
}
}
var _valid0 = _errs7 === errors;
if(_valid0 && valid0){
valid0 = false;
passing0 = [passing0, 1];
}
else {
if(_valid0){
valid0 = true;
passing0 = 1;
if(props1 !== true){
props1 = true;
}
}
const _errs79 = errors;
if(errors === _errs79){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing10;
if((data.kind === undefined) && (missing10 = "kind")){
const err65 = {instancePath,schemaPath:"#/oneOf/2/required",keyword:"required",params:{missingProperty: missing10},message:"must have required property '"+missing10+"'"};
if(vErrors === null){
vErrors = [err65];
}
else {
vErrors.push(err65);
}
errors++;
}
else {
const _errs81 = errors;
for(const key10 in data){
if(!(key10 === "kind")){
const err66 = {instancePath,schemaPath:"#/oneOf/2/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key10},message:"must NOT have additional properties"};
if(vErrors === null){
vErrors = [err66];
}
else {
vErrors.push(err66);
}
errors++;
break;
}
}
if(_errs81 === errors){
if(data.kind !== undefined){
let data24 = data.kind;
if(typeof data24 !== "string"){
const err67 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/2/properties/kind/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err67];
}
else {
vErrors.push(err67);
}
errors++;
}
if("identify" !== data24){
const err68 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/2/properties/kind/const",keyword:"const",params:{allowedValue: "identify"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err68];
}
else {
vErrors.push(err68);
}
errors++;
}
}
}
}
}
else {
const err69 = {instancePath,schemaPath:"#/oneOf/2/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err69];
}
else {
vErrors.push(err69);
}
errors++;
}
}
var _valid0 = _errs79 === errors;
if(_valid0 && valid0){
valid0 = false;
passing0 = [passing0, 2];
}
else {
if(_valid0){
valid0 = true;
passing0 = 2;
if(props1 !== true){
props1 = true;
}
}
const _errs84 = errors;
if(errors === _errs84){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing11;
if((((data.kind === undefined) && (missing11 = "kind")) || ((data.passphrase === undefined) && (missing11 = "passphrase"))) || ((data.create === undefined) && (missing11 = "create"))){
const err70 = {instancePath,schemaPath:"#/oneOf/3/required",keyword:"required",params:{missingProperty: missing11},message:"must have required property '"+missing11+"'"};
if(vErrors === null){
vErrors = [err70];
}
else {
vErrors.push(err70);
}
errors++;
}
else {
const _errs86 = errors;
for(const key11 in data){
if(!(((key11 === "create") || (key11 === "kind")) || (key11 === "passphrase"))){
const err71 = {instancePath,schemaPath:"#/oneOf/3/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key11},message:"must NOT have additional properties"};
if(vErrors === null){
vErrors = [err71];
}
else {
vErrors.push(err71);
}
errors++;
break;
}
}
if(_errs86 === errors){
if(data.create !== undefined){
const _errs87 = errors;
if(typeof data.create !== "boolean"){
const err72 = {instancePath:instancePath+"/create",schemaPath:"#/oneOf/3/properties/create/type",keyword:"type",params:{type: "boolean"},message:"must be boolean"};
if(vErrors === null){
vErrors = [err72];
}
else {
vErrors.push(err72);
}
errors++;
}
var valid14 = _errs87 === errors;
}
else {
var valid14 = true;
}
if(valid14){
if(data.kind !== undefined){
let data26 = data.kind;
const _errs89 = errors;
if(typeof data26 !== "string"){
const err73 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/3/properties/kind/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err73];
}
else {
vErrors.push(err73);
}
errors++;
}
if("unlock" !== data26){
const err74 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/3/properties/kind/const",keyword:"const",params:{allowedValue: "unlock"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err74];
}
else {
vErrors.push(err74);
}
errors++;
}
var valid14 = _errs89 === errors;
}
else {
var valid14 = true;
}
if(valid14){
if(data.passphrase !== undefined){
const _errs91 = errors;
if(typeof data.passphrase !== "string"){
const err75 = {instancePath:instancePath+"/passphrase",schemaPath:"#/oneOf/3/properties/passphrase/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err75];
}
else {
vErrors.push(err75);
}
errors++;
}
var valid14 = _errs91 === errors;
}
else {
var valid14 = true;
}
}
}
}
}
}
else {
const err76 = {instancePath,schemaPath:"#/oneOf/3/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err76];
}
else {
vErrors.push(err76);
}
errors++;
}
}
var _valid0 = _errs84 === errors;
if(_valid0 && valid0){
valid0 = false;
passing0 = [passing0, 3];
}
else {
if(_valid0){
valid0 = true;
passing0 = 3;
if(props1 !== true){
props1 = true;
}
}
const _errs93 = errors;
if(errors === _errs93){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing12;
if((data.kind === undefined) && (missing12 = "kind")){
const err77 = {instancePath,schemaPath:"#/oneOf/4/required",keyword:"required",params:{missingProperty: missing12},message:"must have required property '"+missing12+"'"};
if(vErrors === null){
vErrors = [err77];
}
else {
vErrors.push(err77);
}
errors++;
}
else {
const _errs95 = errors;
for(const key12 in data){
if(!(key12 === "kind")){
const err78 = {instancePath,schemaPath:"#/oneOf/4/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key12},message:"must NOT have additional properties"};
if(vErrors === null){
vErrors = [err78];
}
else {
vErrors.push(err78);
}
errors++;
break;
}
}
if(_errs95 === errors){
if(data.kind !== undefined){
let data28 = data.kind;
if(typeof data28 !== "string"){
const err79 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/4/properties/kind/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err79];
}
else {
vErrors.push(err79);
}
errors++;
}
if("lock" !== data28){
const err80 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/4/properties/kind/const",keyword:"const",params:{allowedValue: "lock"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err80];
}
else {
vErrors.push(err80);
}
errors++;
}
}
}
}
}
else {
const err81 = {instancePath,schemaPath:"#/oneOf/4/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err81];
}
else {
vErrors.push(err81);
}
errors++;
}
}
var _valid0 = _errs93 === errors;
if(_valid0 && valid0){
valid0 = false;
passing0 = [passing0, 4];
}
else {
if(_valid0){
valid0 = true;
passing0 = 4;
if(props1 !== true){
props1 = true;
}
}
const _errs98 = errors;
if(errors === _errs98){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing13;
if((data.kind === undefined) && (missing13 = "kind")){
const err82 = {instancePath,schemaPath:"#/oneOf/5/required",keyword:"required",params:{missingProperty: missing13},message:"must have required property '"+missing13+"'"};
if(vErrors === null){
vErrors = [err82];
}
else {
vErrors.push(err82);
}
errors++;
}
else {
const _errs100 = errors;
for(const key13 in data){
if(!(key13 === "kind")){
const err83 = {instancePath,schemaPath:"#/oneOf/5/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key13},message:"must NOT have additional properties"};
if(vErrors === null){
vErrors = [err83];
}
else {
vErrors.push(err83);
}
errors++;
break;
}
}
if(_errs100 === errors){
if(data.kind !== undefined){
let data29 = data.kind;
if(typeof data29 !== "string"){
const err84 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/5/properties/kind/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err84];
}
else {
vErrors.push(err84);
}
errors++;
}
if("disconnect" !== data29){
const err85 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/5/properties/kind/const",keyword:"const",params:{allowedValue: "disconnect"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err85];
}
else {
vErrors.push(err85);
}
errors++;
}
}
}
}
}
else {
const err86 = {instancePath,schemaPath:"#/oneOf/5/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err86];
}
else {
vErrors.push(err86);
}
errors++;
}
}
var _valid0 = _errs98 === errors;
if(_valid0 && valid0){
valid0 = false;
passing0 = [passing0, 5];
}
else {
if(_valid0){
valid0 = true;
passing0 = 5;
if(props1 !== true){
props1 = true;
}
}
const _errs103 = errors;
if(errors === _errs103){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing14;
if((data.kind === undefined) && (missing14 = "kind")){
const err87 = {instancePath,schemaPath:"#/oneOf/6/required",keyword:"required",params:{missingProperty: missing14},message:"must have required property '"+missing14+"'"};
if(vErrors === null){
vErrors = [err87];
}
else {
vErrors.push(err87);
}
errors++;
}
else {
const _errs105 = errors;
for(const key14 in data){
if(!(key14 === "kind")){
const err88 = {instancePath,schemaPath:"#/oneOf/6/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key14},message:"must NOT have additional properties"};
if(vErrors === null){
vErrors = [err88];
}
else {
vErrors.push(err88);
}
errors++;
break;
}
}
if(_errs105 === errors){
if(data.kind !== undefined){
let data30 = data.kind;
if(typeof data30 !== "string"){
const err89 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/6/properties/kind/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err89];
}
else {
vErrors.push(err89);
}
errors++;
}
if("snapshot" !== data30){
const err90 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/6/properties/kind/const",keyword:"const",params:{allowedValue: "snapshot"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err90];
}
else {
vErrors.push(err90);
}
errors++;
}
}
}
}
}
else {
const err91 = {instancePath,schemaPath:"#/oneOf/6/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err91];
}
else {
vErrors.push(err91);
}
errors++;
}
}
var _valid0 = _errs103 === errors;
if(_valid0 && valid0){
valid0 = false;
passing0 = [passing0, 6];
}
else {
if(_valid0){
valid0 = true;
passing0 = 6;
if(props1 !== true){
props1 = true;
}
}
const _errs108 = errors;
if(errors === _errs108){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing15;
if((data.kind === undefined) && (missing15 = "kind")){
const err92 = {instancePath,schemaPath:"#/oneOf/7/required",keyword:"required",params:{missingProperty: missing15},message:"must have required property '"+missing15+"'"};
if(vErrors === null){
vErrors = [err92];
}
else {
vErrors.push(err92);
}
errors++;
}
else {
const _errs110 = errors;
for(const key15 in data){
if(!(key15 === "kind")){
const err93 = {instancePath,schemaPath:"#/oneOf/7/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key15},message:"must NOT have additional properties"};
if(vErrors === null){
vErrors = [err93];
}
else {
vErrors.push(err93);
}
errors++;
break;
}
}
if(_errs110 === errors){
if(data.kind !== undefined){
let data31 = data.kind;
if(typeof data31 !== "string"){
const err94 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/7/properties/kind/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err94];
}
else {
vErrors.push(err94);
}
errors++;
}
if("network_status" !== data31){
const err95 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/7/properties/kind/const",keyword:"const",params:{allowedValue: "network_status"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err95];
}
else {
vErrors.push(err95);
}
errors++;
}
}
}
}
}
else {
const err96 = {instancePath,schemaPath:"#/oneOf/7/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err96];
}
else {
vErrors.push(err96);
}
errors++;
}
}
var _valid0 = _errs108 === errors;
if(_valid0 && valid0){
valid0 = false;
passing0 = [passing0, 7];
}
else {
if(_valid0){
valid0 = true;
passing0 = 7;
if(props1 !== true){
props1 = true;
}
}
const _errs113 = errors;
if(errors === _errs113){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing16;
if(((data.kind === undefined) && (missing16 = "kind")) || ((data.code === undefined) && (missing16 = "code"))){
const err97 = {instancePath,schemaPath:"#/oneOf/8/required",keyword:"required",params:{missingProperty: missing16},message:"must have required property '"+missing16+"'"};
if(vErrors === null){
vErrors = [err97];
}
else {
vErrors.push(err97);
}
errors++;
}
else {
const _errs115 = errors;
for(const key16 in data){
if(!((key16 === "code") || (key16 === "kind"))){
const err98 = {instancePath,schemaPath:"#/oneOf/8/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key16},message:"must NOT have additional properties"};
if(vErrors === null){
vErrors = [err98];
}
else {
vErrors.push(err98);
}
errors++;
break;
}
}
if(_errs115 === errors){
if(data.code !== undefined){
const _errs116 = errors;
if(typeof data.code !== "string"){
const err99 = {instancePath:instancePath+"/code",schemaPath:"#/oneOf/8/properties/code/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err99];
}
else {
vErrors.push(err99);
}
errors++;
}
var valid19 = _errs116 === errors;
}
else {
var valid19 = true;
}
if(valid19){
if(data.kind !== undefined){
let data33 = data.kind;
const _errs118 = errors;
if(typeof data33 !== "string"){
const err100 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/8/properties/kind/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err100];
}
else {
vErrors.push(err100);
}
errors++;
}
if("import_network_invitation" !== data33){
const err101 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/8/properties/kind/const",keyword:"const",params:{allowedValue: "import_network_invitation"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err101];
}
else {
vErrors.push(err101);
}
errors++;
}
var valid19 = _errs118 === errors;
}
else {
var valid19 = true;
}
}
}
}
}
else {
const err102 = {instancePath,schemaPath:"#/oneOf/8/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err102];
}
else {
vErrors.push(err102);
}
errors++;
}
}
var _valid0 = _errs113 === errors;
if(_valid0 && valid0){
valid0 = false;
passing0 = [passing0, 8];
}
else {
if(_valid0){
valid0 = true;
passing0 = 8;
if(props1 !== true){
props1 = true;
}
}
const _errs120 = errors;
if(errors === _errs120){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing17;
if((data.kind === undefined) && (missing17 = "kind")){
const err103 = {instancePath,schemaPath:"#/oneOf/9/required",keyword:"required",params:{missingProperty: missing17},message:"must have required property '"+missing17+"'"};
if(vErrors === null){
vErrors = [err103];
}
else {
vErrors.push(err103);
}
errors++;
}
else {
const _errs122 = errors;
for(const key17 in data){
if(!((key17 === "conversation") || (key17 === "kind"))){
const err104 = {instancePath,schemaPath:"#/oneOf/9/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key17},message:"must NOT have additional properties"};
if(vErrors === null){
vErrors = [err104];
}
else {
vErrors.push(err104);
}
errors++;
break;
}
}
if(_errs122 === errors){
if(data.conversation !== undefined){
let data34 = data.conversation;
const _errs123 = errors;
if((typeof data34 !== "string") && (data34 !== null)){
const err105 = {instancePath:instancePath+"/conversation",schemaPath:"#/oneOf/9/properties/conversation/type",keyword:"type",params:{type: schema33.oneOf[9].properties.conversation.type},message:"must be string,null"};
if(vErrors === null){
vErrors = [err105];
}
else {
vErrors.push(err105);
}
errors++;
}
var valid20 = _errs123 === errors;
}
else {
var valid20 = true;
}
if(valid20){
if(data.kind !== undefined){
let data35 = data.kind;
const _errs125 = errors;
if(typeof data35 !== "string"){
const err106 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/9/properties/kind/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err106];
}
else {
vErrors.push(err106);
}
errors++;
}
if("catalogue" !== data35){
const err107 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/9/properties/kind/const",keyword:"const",params:{allowedValue: "catalogue"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err107];
}
else {
vErrors.push(err107);
}
errors++;
}
var valid20 = _errs125 === errors;
}
else {
var valid20 = true;
}
}
}
}
}
else {
const err108 = {instancePath,schemaPath:"#/oneOf/9/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err108];
}
else {
vErrors.push(err108);
}
errors++;
}
}
var _valid0 = _errs120 === errors;
if(_valid0 && valid0){
valid0 = false;
passing0 = [passing0, 9];
}
else {
if(_valid0){
valid0 = true;
passing0 = 9;
if(props1 !== true){
props1 = true;
}
}
const _errs127 = errors;
if(errors === _errs127){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing18;
if((((data.kind === undefined) && (missing18 = "kind")) || ((data.conversation === undefined) && (missing18 = "conversation"))) || ((data.limit === undefined) && (missing18 = "limit"))){
const err109 = {instancePath,schemaPath:"#/oneOf/10/required",keyword:"required",params:{missingProperty: missing18},message:"must have required property '"+missing18+"'"};
if(vErrors === null){
vErrors = [err109];
}
else {
vErrors.push(err109);
}
errors++;
}
else {
const _errs129 = errors;
for(const key18 in data){
if(!((((key18 === "before") || (key18 === "conversation")) || (key18 === "kind")) || (key18 === "limit"))){
const err110 = {instancePath,schemaPath:"#/oneOf/10/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key18},message:"must NOT have additional properties"};
if(vErrors === null){
vErrors = [err110];
}
else {
vErrors.push(err110);
}
errors++;
break;
}
}
if(_errs129 === errors){
if(data.before !== undefined){
let data36 = data.before;
const _errs130 = errors;
if((typeof data36 !== "string") && (data36 !== null)){
const err111 = {instancePath:instancePath+"/before",schemaPath:"#/oneOf/10/properties/before/type",keyword:"type",params:{type: schema33.oneOf[10].properties.before.type},message:"must be string,null"};
if(vErrors === null){
vErrors = [err111];
}
else {
vErrors.push(err111);
}
errors++;
}
var valid21 = _errs130 === errors;
}
else {
var valid21 = true;
}
if(valid21){
if(data.conversation !== undefined){
const _errs132 = errors;
if(typeof data.conversation !== "string"){
const err112 = {instancePath:instancePath+"/conversation",schemaPath:"#/oneOf/10/properties/conversation/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err112];
}
else {
vErrors.push(err112);
}
errors++;
}
var valid21 = _errs132 === errors;
}
else {
var valid21 = true;
}
if(valid21){
if(data.kind !== undefined){
let data38 = data.kind;
const _errs134 = errors;
if(typeof data38 !== "string"){
const err113 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/10/properties/kind/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err113];
}
else {
vErrors.push(err113);
}
errors++;
}
if("history" !== data38){
const err114 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/10/properties/kind/const",keyword:"const",params:{allowedValue: "history"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err114];
}
else {
vErrors.push(err114);
}
errors++;
}
var valid21 = _errs134 === errors;
}
else {
var valid21 = true;
}
if(valid21){
if(data.limit !== undefined){
let data39 = data.limit;
const _errs136 = errors;
if(!(((typeof data39 == "number") && (!(data39 % 1) && !isNaN(data39))) && (isFinite(data39)))){
const err115 = {instancePath:instancePath+"/limit",schemaPath:"#/oneOf/10/properties/limit/type",keyword:"type",params:{type: "integer"},message:"must be integer"};
if(vErrors === null){
vErrors = [err115];
}
else {
vErrors.push(err115);
}
errors++;
}
if(errors === _errs136){
if((typeof data39 == "number") && (isFinite(data39))){
if(data39 > 65535 || isNaN(data39)){
const err116 = {instancePath:instancePath+"/limit",schemaPath:"#/oneOf/10/properties/limit/maximum",keyword:"maximum",params:{comparison: "<=", limit: 65535},message:"must be <= 65535"};
if(vErrors === null){
vErrors = [err116];
}
else {
vErrors.push(err116);
}
errors++;
}
else {
if(data39 < 0 || isNaN(data39)){
const err117 = {instancePath:instancePath+"/limit",schemaPath:"#/oneOf/10/properties/limit/minimum",keyword:"minimum",params:{comparison: ">=", limit: 0},message:"must be >= 0"};
if(vErrors === null){
vErrors = [err117];
}
else {
vErrors.push(err117);
}
errors++;
}
}
}
}
var valid21 = _errs136 === errors;
}
else {
var valid21 = true;
}
}
}
}
}
}
}
else {
const err118 = {instancePath,schemaPath:"#/oneOf/10/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err118];
}
else {
vErrors.push(err118);
}
errors++;
}
}
var _valid0 = _errs127 === errors;
if(_valid0 && valid0){
valid0 = false;
passing0 = [passing0, 10];
}
else {
if(_valid0){
valid0 = true;
passing0 = 10;
if(props1 !== true){
props1 = true;
}
}
const _errs138 = errors;
if(errors === _errs138){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing19;
if(((((data.kind === undefined) && (missing19 = "kind")) || ((data.conversation === undefined) && (missing19 = "conversation"))) || ((data.text === undefined) && (missing19 = "text"))) || ((data.limit === undefined) && (missing19 = "limit"))){
const err119 = {instancePath,schemaPath:"#/oneOf/11/required",keyword:"required",params:{missingProperty: missing19},message:"must have required property '"+missing19+"'"};
if(vErrors === null){
vErrors = [err119];
}
else {
vErrors.push(err119);
}
errors++;
}
else {
const _errs140 = errors;
for(const key19 in data){
if(!(((((key19 === "before") || (key19 === "conversation")) || (key19 === "kind")) || (key19 === "limit")) || (key19 === "text"))){
const err120 = {instancePath,schemaPath:"#/oneOf/11/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key19},message:"must NOT have additional properties"};
if(vErrors === null){
vErrors = [err120];
}
else {
vErrors.push(err120);
}
errors++;
break;
}
}
if(_errs140 === errors){
if(data.before !== undefined){
let data40 = data.before;
const _errs141 = errors;
if((typeof data40 !== "string") && (data40 !== null)){
const err121 = {instancePath:instancePath+"/before",schemaPath:"#/oneOf/11/properties/before/type",keyword:"type",params:{type: schema33.oneOf[11].properties.before.type},message:"must be string,null"};
if(vErrors === null){
vErrors = [err121];
}
else {
vErrors.push(err121);
}
errors++;
}
var valid22 = _errs141 === errors;
}
else {
var valid22 = true;
}
if(valid22){
if(data.conversation !== undefined){
const _errs143 = errors;
if(typeof data.conversation !== "string"){
const err122 = {instancePath:instancePath+"/conversation",schemaPath:"#/oneOf/11/properties/conversation/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err122];
}
else {
vErrors.push(err122);
}
errors++;
}
var valid22 = _errs143 === errors;
}
else {
var valid22 = true;
}
if(valid22){
if(data.kind !== undefined){
let data42 = data.kind;
const _errs145 = errors;
if(typeof data42 !== "string"){
const err123 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/11/properties/kind/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err123];
}
else {
vErrors.push(err123);
}
errors++;
}
if("search" !== data42){
const err124 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/11/properties/kind/const",keyword:"const",params:{allowedValue: "search"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err124];
}
else {
vErrors.push(err124);
}
errors++;
}
var valid22 = _errs145 === errors;
}
else {
var valid22 = true;
}
if(valid22){
if(data.limit !== undefined){
let data43 = data.limit;
const _errs147 = errors;
if(!(((typeof data43 == "number") && (!(data43 % 1) && !isNaN(data43))) && (isFinite(data43)))){
const err125 = {instancePath:instancePath+"/limit",schemaPath:"#/oneOf/11/properties/limit/type",keyword:"type",params:{type: "integer"},message:"must be integer"};
if(vErrors === null){
vErrors = [err125];
}
else {
vErrors.push(err125);
}
errors++;
}
if(errors === _errs147){
if((typeof data43 == "number") && (isFinite(data43))){
if(data43 > 65535 || isNaN(data43)){
const err126 = {instancePath:instancePath+"/limit",schemaPath:"#/oneOf/11/properties/limit/maximum",keyword:"maximum",params:{comparison: "<=", limit: 65535},message:"must be <= 65535"};
if(vErrors === null){
vErrors = [err126];
}
else {
vErrors.push(err126);
}
errors++;
}
else {
if(data43 < 0 || isNaN(data43)){
const err127 = {instancePath:instancePath+"/limit",schemaPath:"#/oneOf/11/properties/limit/minimum",keyword:"minimum",params:{comparison: ">=", limit: 0},message:"must be >= 0"};
if(vErrors === null){
vErrors = [err127];
}
else {
vErrors.push(err127);
}
errors++;
}
}
}
}
var valid22 = _errs147 === errors;
}
else {
var valid22 = true;
}
if(valid22){
if(data.text !== undefined){
const _errs149 = errors;
if(typeof data.text !== "string"){
const err128 = {instancePath:instancePath+"/text",schemaPath:"#/oneOf/11/properties/text/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err128];
}
else {
vErrors.push(err128);
}
errors++;
}
var valid22 = _errs149 === errors;
}
else {
var valid22 = true;
}
}
}
}
}
}
}
}
else {
const err129 = {instancePath,schemaPath:"#/oneOf/11/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err129];
}
else {
vErrors.push(err129);
}
errors++;
}
}
var _valid0 = _errs138 === errors;
if(_valid0 && valid0){
valid0 = false;
passing0 = [passing0, 11];
}
else {
if(_valid0){
valid0 = true;
passing0 = 11;
if(props1 !== true){
props1 = true;
}
}
const _errs151 = errors;
if(errors === _errs151){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing20;
if((((data.kind === undefined) && (missing20 = "kind")) || ((data.operation_id === undefined) && (missing20 = "operation_id"))) || ((data.text === undefined) && (missing20 = "text"))){
const err130 = {instancePath,schemaPath:"#/oneOf/12/required",keyword:"required",params:{missingProperty: missing20},message:"must have required property '"+missing20+"'"};
if(vErrors === null){
vErrors = [err130];
}
else {
vErrors.push(err130);
}
errors++;
}
else {
const _errs153 = errors;
for(const key20 in data){
if(!((((key20 === "conversation") || (key20 === "kind")) || (key20 === "operation_id")) || (key20 === "text"))){
const err131 = {instancePath,schemaPath:"#/oneOf/12/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key20},message:"must NOT have additional properties"};
if(vErrors === null){
vErrors = [err131];
}
else {
vErrors.push(err131);
}
errors++;
break;
}
}
if(_errs153 === errors){
if(data.conversation !== undefined){
let data45 = data.conversation;
const _errs154 = errors;
if((typeof data45 !== "string") && (data45 !== null)){
const err132 = {instancePath:instancePath+"/conversation",schemaPath:"#/oneOf/12/properties/conversation/type",keyword:"type",params:{type: schema33.oneOf[12].properties.conversation.type},message:"must be string,null"};
if(vErrors === null){
vErrors = [err132];
}
else {
vErrors.push(err132);
}
errors++;
}
var valid23 = _errs154 === errors;
}
else {
var valid23 = true;
}
if(valid23){
if(data.kind !== undefined){
let data46 = data.kind;
const _errs156 = errors;
if(typeof data46 !== "string"){
const err133 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/12/properties/kind/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err133];
}
else {
vErrors.push(err133);
}
errors++;
}
if("submit" !== data46){
const err134 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/12/properties/kind/const",keyword:"const",params:{allowedValue: "submit"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err134];
}
else {
vErrors.push(err134);
}
errors++;
}
var valid23 = _errs156 === errors;
}
else {
var valid23 = true;
}
if(valid23){
if(data.operation_id !== undefined){
const _errs158 = errors;
if(typeof data.operation_id !== "string"){
const err135 = {instancePath:instancePath+"/operation_id",schemaPath:"#/oneOf/12/properties/operation_id/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err135];
}
else {
vErrors.push(err135);
}
errors++;
}
var valid23 = _errs158 === errors;
}
else {
var valid23 = true;
}
if(valid23){
if(data.text !== undefined){
const _errs160 = errors;
if(typeof data.text !== "string"){
const err136 = {instancePath:instancePath+"/text",schemaPath:"#/oneOf/12/properties/text/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err136];
}
else {
vErrors.push(err136);
}
errors++;
}
var valid23 = _errs160 === errors;
}
else {
var valid23 = true;
}
}
}
}
}
}
}
else {
const err137 = {instancePath,schemaPath:"#/oneOf/12/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err137];
}
else {
vErrors.push(err137);
}
errors++;
}
}
var _valid0 = _errs151 === errors;
if(_valid0 && valid0){
valid0 = false;
passing0 = [passing0, 12];
}
else {
if(_valid0){
valid0 = true;
passing0 = 12;
if(props1 !== true){
props1 = true;
}
}
const _errs162 = errors;
if(errors === _errs162){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing21;
if(((data.kind === undefined) && (missing21 = "kind")) || ((data.text === undefined) && (missing21 = "text"))){
const err138 = {instancePath,schemaPath:"#/oneOf/13/required",keyword:"required",params:{missingProperty: missing21},message:"must have required property '"+missing21+"'"};
if(vErrors === null){
vErrors = [err138];
}
else {
vErrors.push(err138);
}
errors++;
}
else {
const _errs164 = errors;
for(const key21 in data){
if(!(((key21 === "conversation") || (key21 === "kind")) || (key21 === "text"))){
const err139 = {instancePath,schemaPath:"#/oneOf/13/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key21},message:"must NOT have additional properties"};
if(vErrors === null){
vErrors = [err139];
}
else {
vErrors.push(err139);
}
errors++;
break;
}
}
if(_errs164 === errors){
if(data.conversation !== undefined){
let data49 = data.conversation;
const _errs165 = errors;
if((typeof data49 !== "string") && (data49 !== null)){
const err140 = {instancePath:instancePath+"/conversation",schemaPath:"#/oneOf/13/properties/conversation/type",keyword:"type",params:{type: schema33.oneOf[13].properties.conversation.type},message:"must be string,null"};
if(vErrors === null){
vErrors = [err140];
}
else {
vErrors.push(err140);
}
errors++;
}
var valid24 = _errs165 === errors;
}
else {
var valid24 = true;
}
if(valid24){
if(data.kind !== undefined){
let data50 = data.kind;
const _errs167 = errors;
if(typeof data50 !== "string"){
const err141 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/13/properties/kind/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err141];
}
else {
vErrors.push(err141);
}
errors++;
}
if("complete" !== data50){
const err142 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/13/properties/kind/const",keyword:"const",params:{allowedValue: "complete"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err142];
}
else {
vErrors.push(err142);
}
errors++;
}
var valid24 = _errs167 === errors;
}
else {
var valid24 = true;
}
if(valid24){
if(data.text !== undefined){
const _errs169 = errors;
if(typeof data.text !== "string"){
const err143 = {instancePath:instancePath+"/text",schemaPath:"#/oneOf/13/properties/text/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err143];
}
else {
vErrors.push(err143);
}
errors++;
}
var valid24 = _errs169 === errors;
}
else {
var valid24 = true;
}
}
}
}
}
}
else {
const err144 = {instancePath,schemaPath:"#/oneOf/13/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err144];
}
else {
vErrors.push(err144);
}
errors++;
}
}
var _valid0 = _errs162 === errors;
if(_valid0 && valid0){
valid0 = false;
passing0 = [passing0, 13];
}
else {
if(_valid0){
valid0 = true;
passing0 = 13;
if(props1 !== true){
props1 = true;
}
}
const _errs171 = errors;
if(errors === _errs171){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing22;
if((((data.kind === undefined) && (missing22 = "kind")) || ((data.conversation === undefined) && (missing22 = "conversation"))) || ((data.message_id === undefined) && (missing22 = "message_id"))){
const err145 = {instancePath,schemaPath:"#/oneOf/14/required",keyword:"required",params:{missingProperty: missing22},message:"must have required property '"+missing22+"'"};
if(vErrors === null){
vErrors = [err145];
}
else {
vErrors.push(err145);
}
errors++;
}
else {
const _errs173 = errors;
for(const key22 in data){
if(!(((key22 === "conversation") || (key22 === "kind")) || (key22 === "message_id"))){
const err146 = {instancePath,schemaPath:"#/oneOf/14/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key22},message:"must NOT have additional properties"};
if(vErrors === null){
vErrors = [err146];
}
else {
vErrors.push(err146);
}
errors++;
break;
}
}
if(_errs173 === errors){
if(data.conversation !== undefined){
const _errs174 = errors;
if(typeof data.conversation !== "string"){
const err147 = {instancePath:instancePath+"/conversation",schemaPath:"#/oneOf/14/properties/conversation/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err147];
}
else {
vErrors.push(err147);
}
errors++;
}
var valid25 = _errs174 === errors;
}
else {
var valid25 = true;
}
if(valid25){
if(data.kind !== undefined){
let data53 = data.kind;
const _errs176 = errors;
if(typeof data53 !== "string"){
const err148 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/14/properties/kind/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err148];
}
else {
vErrors.push(err148);
}
errors++;
}
if("mark_read" !== data53){
const err149 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/14/properties/kind/const",keyword:"const",params:{allowedValue: "mark_read"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err149];
}
else {
vErrors.push(err149);
}
errors++;
}
var valid25 = _errs176 === errors;
}
else {
var valid25 = true;
}
if(valid25){
if(data.message_id !== undefined){
const _errs178 = errors;
if(typeof data.message_id !== "string"){
const err150 = {instancePath:instancePath+"/message_id",schemaPath:"#/oneOf/14/properties/message_id/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err150];
}
else {
vErrors.push(err150);
}
errors++;
}
var valid25 = _errs178 === errors;
}
else {
var valid25 = true;
}
}
}
}
}
}
else {
const err151 = {instancePath,schemaPath:"#/oneOf/14/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err151];
}
else {
vErrors.push(err151);
}
errors++;
}
}
var _valid0 = _errs171 === errors;
if(_valid0 && valid0){
valid0 = false;
passing0 = [passing0, 14];
}
else {
if(_valid0){
valid0 = true;
passing0 = 14;
if(props1 !== true){
props1 = true;
}
}
const _errs180 = errors;
if(errors === _errs180){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing23;
if((((data.kind === undefined) && (missing23 = "kind")) || ((data.after === undefined) && (missing23 = "after"))) || ((data.wait_ms === undefined) && (missing23 = "wait_ms"))){
const err152 = {instancePath,schemaPath:"#/oneOf/15/required",keyword:"required",params:{missingProperty: missing23},message:"must have required property '"+missing23+"'"};
if(vErrors === null){
vErrors = [err152];
}
else {
vErrors.push(err152);
}
errors++;
}
else {
const _errs182 = errors;
for(const key23 in data){
if(!(((key23 === "after") || (key23 === "kind")) || (key23 === "wait_ms"))){
const err153 = {instancePath,schemaPath:"#/oneOf/15/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key23},message:"must NOT have additional properties"};
if(vErrors === null){
vErrors = [err153];
}
else {
vErrors.push(err153);
}
errors++;
break;
}
}
if(_errs182 === errors){
if(data.after !== undefined){
const _errs183 = errors;
if(typeof data.after !== "string"){
const err154 = {instancePath:instancePath+"/after",schemaPath:"#/oneOf/15/properties/after/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err154];
}
else {
vErrors.push(err154);
}
errors++;
}
var valid26 = _errs183 === errors;
}
else {
var valid26 = true;
}
if(valid26){
if(data.kind !== undefined){
let data56 = data.kind;
const _errs185 = errors;
if(typeof data56 !== "string"){
const err155 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/15/properties/kind/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err155];
}
else {
vErrors.push(err155);
}
errors++;
}
if("events" !== data56){
const err156 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/15/properties/kind/const",keyword:"const",params:{allowedValue: "events"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err156];
}
else {
vErrors.push(err156);
}
errors++;
}
var valid26 = _errs185 === errors;
}
else {
var valid26 = true;
}
if(valid26){
if(data.wait_ms !== undefined){
let data57 = data.wait_ms;
const _errs187 = errors;
if(!(((typeof data57 == "number") && (!(data57 % 1) && !isNaN(data57))) && (isFinite(data57)))){
const err157 = {instancePath:instancePath+"/wait_ms",schemaPath:"#/oneOf/15/properties/wait_ms/type",keyword:"type",params:{type: "integer"},message:"must be integer"};
if(vErrors === null){
vErrors = [err157];
}
else {
vErrors.push(err157);
}
errors++;
}
if(errors === _errs187){
if((typeof data57 == "number") && (isFinite(data57))){
if(data57 > 65535 || isNaN(data57)){
const err158 = {instancePath:instancePath+"/wait_ms",schemaPath:"#/oneOf/15/properties/wait_ms/maximum",keyword:"maximum",params:{comparison: "<=", limit: 65535},message:"must be <= 65535"};
if(vErrors === null){
vErrors = [err158];
}
else {
vErrors.push(err158);
}
errors++;
}
else {
if(data57 < 0 || isNaN(data57)){
const err159 = {instancePath:instancePath+"/wait_ms",schemaPath:"#/oneOf/15/properties/wait_ms/minimum",keyword:"minimum",params:{comparison: ">=", limit: 0},message:"must be >= 0"};
if(vErrors === null){
vErrors = [err159];
}
else {
vErrors.push(err159);
}
errors++;
}
}
}
}
var valid26 = _errs187 === errors;
}
else {
var valid26 = true;
}
}
}
}
}
}
else {
const err160 = {instancePath,schemaPath:"#/oneOf/15/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err160];
}
else {
vErrors.push(err160);
}
errors++;
}
}
var _valid0 = _errs180 === errors;
if(_valid0 && valid0){
valid0 = false;
passing0 = [passing0, 15];
}
else {
if(_valid0){
valid0 = true;
passing0 = 15;
if(props1 !== true){
props1 = true;
}
}
}
}
}
}
}
}
}
}
}
}
}
}
}
}
}
if(!valid0){
const err161 = {instancePath,schemaPath:"#/oneOf",keyword:"oneOf",params:{passingSchemas: passing0},message:"must match exactly one schema in oneOf"};
if(vErrors === null){
vErrors = [err161];
}
else {
vErrors.push(err161);
}
errors++;
validate22.errors = vErrors;
return false;
}
else {
errors = _errs0;
if(vErrors !== null){
if(_errs0){
vErrors.length = _errs0;
}
else {
vErrors = null;
}
}
}
validate22.errors = vErrors;
evaluated0.props = props1;
return errors === 0;
}
validate22.evaluated = {"dynamicProps":true,"dynamicItems":false};


function validate21(data, {instancePath="", parentData, parentDataProperty, rootData=data, dynamicAnchors={}}={}){
let vErrors = null;
let errors = 0;
const evaluated0 = validate21.evaluated;
if(evaluated0.dynamicProps){
evaluated0.props = undefined;
}
if(evaluated0.dynamicItems){
evaluated0.items = undefined;
}
const _errs0 = errors;
let valid0 = false;
let passing0 = null;
const _errs1 = errors;
if(errors === _errs1){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing0;
if((data.kind === undefined) && (missing0 = "kind")){
const err0 = {instancePath,schemaPath:"#/oneOf/0/required",keyword:"required",params:{missingProperty: missing0},message:"must have required property '"+missing0+"'"};
if(vErrors === null){
vErrors = [err0];
}
else {
vErrors.push(err0);
}
errors++;
}
else {
const _errs3 = errors;
for(const key0 in data){
if(!(key0 === "kind")){
const err1 = {instancePath,schemaPath:"#/oneOf/0/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key0},message:"must NOT have additional properties"};
if(vErrors === null){
vErrors = [err1];
}
else {
vErrors.push(err1);
}
errors++;
break;
}
}
if(_errs3 === errors){
if(data.kind !== undefined){
let data0 = data.kind;
if(typeof data0 !== "string"){
const err2 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/0/properties/kind/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err2];
}
else {
vErrors.push(err2);
}
errors++;
}
if("list" !== data0){
const err3 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/0/properties/kind/const",keyword:"const",params:{allowedValue: "list"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err3];
}
else {
vErrors.push(err3);
}
errors++;
}
}
}
}
}
else {
const err4 = {instancePath,schemaPath:"#/oneOf/0/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err4];
}
else {
vErrors.push(err4);
}
errors++;
}
}
var _valid0 = _errs1 === errors;
if(_valid0){
valid0 = true;
passing0 = 0;
var props0 = true;
}
const _errs6 = errors;
if(errors === _errs6){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing1;
if(((data.kind === undefined) && (missing1 = "kind")) || ((data.code === undefined) && (missing1 = "code"))){
const err5 = {instancePath,schemaPath:"#/oneOf/1/required",keyword:"required",params:{missingProperty: missing1},message:"must have required property '"+missing1+"'"};
if(vErrors === null){
vErrors = [err5];
}
else {
vErrors.push(err5);
}
errors++;
}
else {
const _errs8 = errors;
for(const key1 in data){
if(!((key1 === "code") || (key1 === "kind"))){
const err6 = {instancePath,schemaPath:"#/oneOf/1/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key1},message:"must NOT have additional properties"};
if(vErrors === null){
vErrors = [err6];
}
else {
vErrors.push(err6);
}
errors++;
break;
}
}
if(_errs8 === errors){
if(data.code !== undefined){
const _errs9 = errors;
if(typeof data.code !== "string"){
const err7 = {instancePath:instancePath+"/code",schemaPath:"#/oneOf/1/properties/code/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err7];
}
else {
vErrors.push(err7);
}
errors++;
}
var valid2 = _errs9 === errors;
}
else {
var valid2 = true;
}
if(valid2){
if(data.kind !== undefined){
let data2 = data.kind;
const _errs11 = errors;
if(typeof data2 !== "string"){
const err8 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/1/properties/kind/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err8];
}
else {
vErrors.push(err8);
}
errors++;
}
if("inspect" !== data2){
const err9 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/1/properties/kind/const",keyword:"const",params:{allowedValue: "inspect"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err9];
}
else {
vErrors.push(err9);
}
errors++;
}
var valid2 = _errs11 === errors;
}
else {
var valid2 = true;
}
}
}
}
}
else {
const err10 = {instancePath,schemaPath:"#/oneOf/1/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err10];
}
else {
vErrors.push(err10);
}
errors++;
}
}
var _valid0 = _errs6 === errors;
if(_valid0 && valid0){
valid0 = false;
passing0 = [passing0, 1];
}
else {
if(_valid0){
valid0 = true;
passing0 = 1;
if(props0 !== true){
props0 = true;
}
}
const _errs13 = errors;
if(errors === _errs13){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing2;
if((((((data.kind === undefined) && (missing2 = "kind")) || ((data.code === undefined) && (missing2 = "code"))) || ((data.nickname === undefined) && (missing2 = "nickname"))) || ((data.accepted_network === undefined) && (missing2 = "accepted_network"))) || ((data.operation_id === undefined) && (missing2 = "operation_id"))){
const err11 = {instancePath,schemaPath:"#/oneOf/2/required",keyword:"required",params:{missingProperty: missing2},message:"must have required property '"+missing2+"'"};
if(vErrors === null){
vErrors = [err11];
}
else {
vErrors.push(err11);
}
errors++;
}
else {
const _errs15 = errors;
for(const key2 in data){
if(!(((((key2 === "accepted_network") || (key2 === "code")) || (key2 === "kind")) || (key2 === "nickname")) || (key2 === "operation_id"))){
const err12 = {instancePath,schemaPath:"#/oneOf/2/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key2},message:"must NOT have additional properties"};
if(vErrors === null){
vErrors = [err12];
}
else {
vErrors.push(err12);
}
errors++;
break;
}
}
if(_errs15 === errors){
if(data.accepted_network !== undefined){
const _errs16 = errors;
if(typeof data.accepted_network !== "string"){
const err13 = {instancePath:instancePath+"/accepted_network",schemaPath:"#/oneOf/2/properties/accepted_network/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err13];
}
else {
vErrors.push(err13);
}
errors++;
}
var valid3 = _errs16 === errors;
}
else {
var valid3 = true;
}
if(valid3){
if(data.code !== undefined){
const _errs18 = errors;
if(typeof data.code !== "string"){
const err14 = {instancePath:instancePath+"/code",schemaPath:"#/oneOf/2/properties/code/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err14];
}
else {
vErrors.push(err14);
}
errors++;
}
var valid3 = _errs18 === errors;
}
else {
var valid3 = true;
}
if(valid3){
if(data.kind !== undefined){
let data5 = data.kind;
const _errs20 = errors;
if(typeof data5 !== "string"){
const err15 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/2/properties/kind/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err15];
}
else {
vErrors.push(err15);
}
errors++;
}
if("join" !== data5){
const err16 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/2/properties/kind/const",keyword:"const",params:{allowedValue: "join"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err16];
}
else {
vErrors.push(err16);
}
errors++;
}
var valid3 = _errs20 === errors;
}
else {
var valid3 = true;
}
if(valid3){
if(data.nickname !== undefined){
const _errs22 = errors;
if(typeof data.nickname !== "string"){
const err17 = {instancePath:instancePath+"/nickname",schemaPath:"#/oneOf/2/properties/nickname/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err17];
}
else {
vErrors.push(err17);
}
errors++;
}
var valid3 = _errs22 === errors;
}
else {
var valid3 = true;
}
if(valid3){
if(data.operation_id !== undefined){
const _errs24 = errors;
if(typeof data.operation_id !== "string"){
const err18 = {instancePath:instancePath+"/operation_id",schemaPath:"#/oneOf/2/properties/operation_id/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err18];
}
else {
vErrors.push(err18);
}
errors++;
}
var valid3 = _errs24 === errors;
}
else {
var valid3 = true;
}
}
}
}
}
}
}
}
else {
const err19 = {instancePath,schemaPath:"#/oneOf/2/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err19];
}
else {
vErrors.push(err19);
}
errors++;
}
}
var _valid0 = _errs13 === errors;
if(_valid0 && valid0){
valid0 = false;
passing0 = [passing0, 2];
}
else {
if(_valid0){
valid0 = true;
passing0 = 2;
if(props0 !== true){
props0 = true;
}
}
const _errs26 = errors;
if(errors === _errs26){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing3;
if((((data.kind === undefined) && (missing3 = "kind")) || ((data.network === undefined) && (missing3 = "network"))) || ((data.request === undefined) && (missing3 = "request"))){
const err20 = {instancePath,schemaPath:"#/oneOf/3/required",keyword:"required",params:{missingProperty: missing3},message:"must have required property '"+missing3+"'"};
if(vErrors === null){
vErrors = [err20];
}
else {
vErrors.push(err20);
}
errors++;
}
else {
const _errs28 = errors;
for(const key3 in data){
if(!(((key3 === "kind") || (key3 === "network")) || (key3 === "request"))){
const err21 = {instancePath,schemaPath:"#/oneOf/3/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key3},message:"must NOT have additional properties"};
if(vErrors === null){
vErrors = [err21];
}
else {
vErrors.push(err21);
}
errors++;
break;
}
}
if(_errs28 === errors){
if(data.kind !== undefined){
let data8 = data.kind;
const _errs29 = errors;
if(typeof data8 !== "string"){
const err22 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/3/properties/kind/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err22];
}
else {
vErrors.push(err22);
}
errors++;
}
if("call" !== data8){
const err23 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/3/properties/kind/const",keyword:"const",params:{allowedValue: "call"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err23];
}
else {
vErrors.push(err23);
}
errors++;
}
var valid4 = _errs29 === errors;
}
else {
var valid4 = true;
}
if(valid4){
if(data.network !== undefined){
const _errs31 = errors;
if(typeof data.network !== "string"){
const err24 = {instancePath:instancePath+"/network",schemaPath:"#/oneOf/3/properties/network/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err24];
}
else {
vErrors.push(err24);
}
errors++;
}
var valid4 = _errs31 === errors;
}
else {
var valid4 = true;
}
if(valid4){
if(data.request !== undefined){
const _errs33 = errors;
if(!(validate22(data.request, {instancePath:instancePath+"/request",parentData:data,parentDataProperty:"request",rootData,dynamicAnchors}))){
vErrors = vErrors === null ? validate22.errors : vErrors.concat(validate22.errors);
errors = vErrors.length;
}
var valid4 = _errs33 === errors;
}
else {
var valid4 = true;
}
}
}
}
}
}
else {
const err25 = {instancePath,schemaPath:"#/oneOf/3/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err25];
}
else {
vErrors.push(err25);
}
errors++;
}
}
var _valid0 = _errs26 === errors;
if(_valid0 && valid0){
valid0 = false;
passing0 = [passing0, 3];
}
else {
if(_valid0){
valid0 = true;
passing0 = 3;
if(props0 !== true){
props0 = true;
}
}
}
}
}
if(!valid0){
const err26 = {instancePath,schemaPath:"#/oneOf",keyword:"oneOf",params:{passingSchemas: passing0},message:"must match exactly one schema in oneOf"};
if(vErrors === null){
vErrors = [err26];
}
else {
vErrors.push(err26);
}
errors++;
validate21.errors = vErrors;
return false;
}
else {
errors = _errs0;
if(vErrors !== null){
if(_errs0){
vErrors.length = _errs0;
}
else {
vErrors = null;
}
}
}
validate21.errors = vErrors;
evaluated0.props = props0;
return errors === 0;
}
validate21.evaluated = {"dynamicProps":true,"dynamicItems":false};


function validate20(data, {instancePath="", parentData, parentDataProperty, rootData=data, dynamicAnchors={}}={}){
let vErrors = null;
let errors = 0;
const evaluated0 = validate20.evaluated;
if(evaluated0.dynamicProps){
evaluated0.props = undefined;
}
if(evaluated0.dynamicItems){
evaluated0.items = undefined;
}
if(errors === 0){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing0;
if((data.request === undefined) && (missing0 = "request")){
validate20.errors = [{instancePath,schemaPath:"#/required",keyword:"required",params:{missingProperty: missing0},message:"must have required property '"+missing0+"'"}];
return false;
}
else {
const _errs1 = errors;
for(const key0 in data){
if(!(key0 === "request")){
validate20.errors = [{instancePath,schemaPath:"#/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key0},message:"must NOT have additional properties"}];
return false;
break;
}
}
if(_errs1 === errors){
if(data.request !== undefined){
if(!(validate21(data.request, {instancePath:instancePath+"/request",parentData:data,parentDataProperty:"request",rootData,dynamicAnchors}))){
vErrors = vErrors === null ? validate21.errors : vErrors.concat(validate21.errors);
errors = vErrors.length;
}
}
}
}
}
else {
validate20.errors = [{instancePath,schemaPath:"#/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
validate20.errors = vErrors;
return errors === 0;
}
validate20.evaluated = {"props":true,"dynamicProps":false,"dynamicItems":false};

export const network_operation_output = validate25;
const schema35 = {"$defs":{"ActionResult":{"properties":{"artifacts":{"items":{"$ref":"#/$defs/Artifact"},"type":"array"},"details":{"items":{"type":"string"},"type":"array"},"id":{"type":"string"},"messageId":{"default":null,"type":["string","null"]},"outputBase64":{"description":"Exact signed bytes, base64 encoded; views decode only for display.","type":["string","null"]},"state":{"type":"string"},"stderr":{"type":"boolean"}},"required":["id","state","stderr","details","artifacts"],"type":"object"},"Activity":{"description":"Authenticated state changes observed by this profile, retained before publication.","properties":{"conversation":{"type":"string"},"id":{"type":"string"},"kind":{"type":"string"},"text":{"type":"string"},"timestamp":{"format":"uint64","minimum":0,"type":"integer"}},"required":["id","conversation","kind","text","timestamp"],"type":"object"},"Artifact":{"properties":{"name":{"type":"string"},"url":{"type":"string"}},"required":["name","url"],"type":"object"},"CommandOutput":{"oneOf":[{"properties":{"commands":{"items":{"$ref":"#/$defs/CommandSpec"},"type":"array"},"kind":{"const":"help","type":"string"}},"required":["kind","commands"],"type":"object"},{"properties":{"channels":{"items":{"$ref":"#/$defs/DirectoryEntry"},"type":"array"},"kind":{"const":"directory","type":"string"}},"required":["kind","channels"],"type":"object"},{"properties":{"channel":{"type":"string"},"expires":{"format":"uint64","minimum":0,"type":"integer"},"kind":{"const":"invitation","type":"string"},"link":{"type":"string"},"localOnly":{"default":false,"type":"boolean"}},"required":["kind","channel","link","expires"],"type":"object"},{"properties":{"kind":{"const":"text","type":"string"},"text":{"type":"string"},"title":{"type":"string"}},"required":["kind","title","text"],"type":"object"},{"properties":{"kind":{"const":"status","type":"string"},"text":{"type":"string"}},"required":["kind","text"],"type":"object"},{"properties":{"conversation":{"type":"string"},"kind":{"const":"close","type":"string"}},"required":["kind","conversation"],"type":"object"}]},"CommandSpec":{"properties":{"available":{"type":"boolean"},"capability":{"type":["string","null"]},"description":{"type":"string"},"name":{"type":"string"},"scope":{"type":"string"},"usage":{"type":"string"}},"required":["name","usage","description","scope","available"],"type":"object"},"Completion":{"properties":{"description":{"type":"string"},"text":{"type":"string"}},"required":["text","description"],"type":"object"},"Conversation":{"properties":{"active":{"type":"boolean"},"channelId":{"type":"string"},"commands":{"default":[],"items":{"$ref":"#/$defs/CommandSpec"},"type":"array"},"directory":{"default":null,"type":["string","null"]},"id":{"type":"string"},"inputLimitBytes":{"default":12000,"format":"uint","minimum":0,"type":"integer"},"kind":{"$ref":"#/$defs/ConversationKind"},"lastMessageId":{"type":["string","null"]},"members":{"items":{"$ref":"#/$defs/Member"},"type":"array"},"name":{"type":"string"},"owner":{"type":"boolean"},"provider":{"default":null,"type":["string","null"]},"topic":{"type":"string"},"unread":{"format":"uint32","minimum":0,"type":"integer"},"visibility":{"default":null,"type":["string","null"]}},"required":["id","channelId","kind","name","topic","active","owner","members","unread"],"type":"object"},"ConversationKind":{"enum":["channel","query","archive"],"type":"string"},"Delivery":{"enum":["local_accepted","delivered"],"type":"string"},"DirectoryEntry":{"properties":{"conversation":{"type":["string","null"]},"joined":{"type":"boolean"},"name":{"type":"string"}},"required":["name","joined"],"type":"object"},"FileInfo":{"additionalProperties":false,"properties":{"aliases":{"default":null,"items":{"type":"string"},"type":["array","null"]},"completed_by":{"format":"uint16","maximum":65535,"minimum":0,"type":"integer"},"conversation":{"type":"string"},"error":{"type":["string","null"]},"id":{"type":"string"},"name":{"type":"string"},"size_bytes":{"type":"string"},"sources":{"format":"uint16","maximum":65535,"minimum":0,"type":"integer"},"state":{"$ref":"#/$defs/FileState"},"verified_bytes":{"type":"string"},"verified_sources":{"default":0,"description":"Peers contributing verified pieces since this process opened the cache.","format":"uint16","maximum":65535,"minimum":0,"type":"integer"}},"required":["id","conversation","name","size_bytes","verified_bytes","state","sources","completed_by"],"type":"object"},"FileSnapshot":{"additionalProperties":false,"properties":{"files":{"items":{"$ref":"#/$defs/FileInfo"},"type":"array"},"quota_bytes":{"type":"string"},"retention_days":{"format":"uint16","maximum":65535,"minimum":0,"type":"integer"},"used_bytes":{"type":"string"}},"required":["files","quota_bytes","used_bytes","retention_days"],"type":"object"},"FileState":{"enum":["offered","importing","downloading","waiting_for_peers","paused","complete","failed","cancelled"],"type":"string"},"HistoryPage":{"properties":{"before":{"type":["string","null"]},"messages":{"items":{"$ref":"#/$defs/Message"},"type":"array"}},"required":["messages"],"type":"object"},"InputHistoryEntry":{"properties":{"conversation":{"type":["string","null"]},"text":{"type":"string"}},"required":["text"],"type":"object"},"InstanceInfo":{"properties":{"archiveExists":{"type":"boolean"},"bootId":{"type":"string"},"capabilities":{"items":{"type":"string"},"type":"array"},"id":{"type":"string"},"label":{"type":"string"},"locked":{"type":"boolean"},"profileExists":{"type":"boolean"},"protocolLocked":{"type":"boolean"},"safetyNumber":{"type":"string"}},"required":["id","label","bootId","locked","protocolLocked","profileExists","archiveExists","safetyNumber","capabilities"],"type":"object"},"InvitationPreview":{"properties":{"channel":{"type":["string","null"]},"expires":{"format":"uint64","minimum":0,"type":"integer"},"network":{"$ref":"#/$defs/JoinedNetwork"},"newNetwork":{"type":"boolean"}},"required":["network","newNetwork","expires"],"type":"object"},"JoinedNetwork":{"properties":{"fingerprint":{"type":"string"},"id":{"type":"string"},"name":{"type":"string"},"primary":{"type":"boolean"},"status":{"$ref":"#/$defs/NetworkStatus"}},"required":["id","name","fingerprint","primary","status"],"type":"object"},"Member":{"properties":{"capabilities":{"default":[],"items":{"type":"string"},"type":"array"},"id":{"type":"string"},"isSelf":{"type":"boolean"},"nickname":{"type":"string"},"recentlyActive":{"default":null,"type":["boolean","null"]}},"required":["id","nickname","isSelf"],"type":"object"},"Message":{"properties":{"body":{"type":"string"},"conversationId":{"type":"string"},"delivery":{"anyOf":[{"$ref":"#/$defs/Delivery"},{"type":"null"}],"description":"Delivered is an authenticated recipient acknowledgement, never a read receipt."},"id":{"type":"string"},"memberId":{"type":["string","null"]},"mine":{"type":"boolean"},"nickname":{"type":"string"},"operationId":{"default":null,"type":["string","null"]},"result":{"anyOf":[{"$ref":"#/$defs/ActionResult"},{"type":"null"}],"default":null},"timestamp":{"format":"uint64","minimum":0,"type":"integer"}},"required":["id","conversationId","nickname","body","timestamp","mine"],"type":"object"},"NetworkState":{"description":"Public connection progress; never contains invitations or private routing cards.","enum":["locked","local_only","invitation_required","connecting","connected","reconnecting","invitation_expired","unavailable"],"type":"string"},"NetworkStatus":{"properties":{"message":{"type":"string"},"state":{"$ref":"#/$defs/NetworkState"}},"required":["state","message"],"type":"object"},"OperationDetail":{"description":"Safe metadata plus the protected result retained in the encrypted operation journal.","properties":{"action":{"type":"string"},"conversation":{"type":["string","null"]},"id":{"type":"string"},"instance":{"type":"string"},"message":{"type":["string","null"]},"network":{"default":null,"type":["string","null"]},"output":{"anyOf":[{"$ref":"#/$defs/CommandOutput"},{"type":"null"}]},"started":{"format":"uint64","minimum":0,"type":"integer"},"state":{"type":"string"}},"required":["id","instance","action","started","state"],"type":"object"},"ProviderStatus":{"properties":{"code":{"type":"string"},"id":{"type":"string"},"message":{"type":"string"},"retryable":{"type":"boolean"}},"required":["id","code","message","retryable"],"type":"object"},"Response":{"oneOf":[{"properties":{"kind":{"const":"networks","type":"string"},"response":{"$ref":"#"}},"required":["kind","response"],"type":"object"},{"properties":{"kind":{"const":"files","type":"string"},"snapshot":{"$ref":"#/$defs/FileSnapshot"}},"required":["kind","snapshot"],"type":"object"},{"properties":{"kind":{"const":"network_status","type":"string"},"status":{"$ref":"#/$defs/NetworkStatus"}},"required":["kind","status"],"type":"object"},{"properties":{"instance":{"$ref":"#/$defs/InstanceInfo"},"kind":{"const":"instance","type":"string"}},"required":["kind","instance"],"type":"object"},{"properties":{"kind":{"const":"snapshot","type":"string"},"snapshot":{"$ref":"#/$defs/Snapshot"}},"required":["kind","snapshot"],"type":"object"},{"properties":{"kind":{"const":"history","type":"string"},"page":{"$ref":"#/$defs/HistoryPage"}},"required":["kind","page"],"type":"object"},{"properties":{"items":{"items":{"$ref":"#/$defs/Completion"},"type":"array"},"kind":{"const":"completed","type":"string"}},"required":["kind","items"],"type":"object"},{"properties":{"commands":{"items":{"$ref":"#/$defs/CommandSpec"},"type":"array"},"kind":{"const":"catalogue","type":"string"}},"required":["kind","commands"],"type":"object"},{"properties":{"conversations":{"items":{"$ref":"#/$defs/Conversation"},"type":"array"},"kind":{"const":"projection","type":"string"},"revision":{"type":"string"}},"required":["kind","conversations","revision"],"type":"object"},{"properties":{"conversation":{"type":["string","null"]},"kind":{"const":"output","type":"string"},"output":{"$ref":"#/$defs/CommandOutput"}},"required":["kind","output"],"type":"object"},{"properties":{"conversation":{"type":["string","null"]},"kind":{"const":"applied","type":"string"},"notice":{"type":["string","null"]}},"required":["kind"],"type":"object"},{"properties":{"kind":{"const":"changed","type":"string"},"revision":{"type":"string"}},"required":["kind","revision"],"type":"object"},{"properties":{"code":{"type":"string"},"kind":{"const":"error","type":"string"},"message":{"type":"string"}},"required":["kind","code","message"],"type":"object"}]},"Snapshot":{"properties":{"activity":{"default":null,"items":{"$ref":"#/$defs/Activity"},"type":["array","null"]},"commandHistory":{"items":{"type":"string"},"type":"array"},"conversations":{"items":{"$ref":"#/$defs/Conversation"},"type":"array"},"inputHistory":{"items":{"$ref":"#/$defs/InputHistoryEntry"},"type":"array"},"instance":{"$ref":"#/$defs/InstanceInfo"},"operations":{"default":null,"items":{"$ref":"#/$defs/OperationDetail"},"type":["array","null"]},"presenceEnabled":{"default":null,"type":["boolean","null"]},"providerErrors":{"default":[],"items":{"$ref":"#/$defs/ProviderStatus"},"type":"array"},"revision":{"type":"string"}},"required":["instance","revision","conversations","commandHistory","inputHistory"],"type":"object"}},"$schema":"https://json-schema.org/draft/2020-12/schema","oneOf":[{"properties":{"kind":{"const":"list","type":"string"},"networks":{"items":{"$ref":"#/$defs/JoinedNetwork"},"type":"array"}},"required":["kind","networks"],"type":"object"},{"properties":{"kind":{"const":"preview","type":"string"},"preview":{"$ref":"#/$defs/InvitationPreview"}},"required":["kind","preview"],"type":"object"},{"properties":{"kind":{"const":"result","type":"string"},"network":{"type":"string"},"response":{"$ref":"#/$defs/Response"}},"required":["kind","network","response"],"type":"object"}],"title":"NetworkResponse"};
const schema36 = {"properties":{"fingerprint":{"type":"string"},"id":{"type":"string"},"name":{"type":"string"},"primary":{"type":"boolean"},"status":{"$ref":"#/$defs/NetworkStatus"}},"required":["id","name","fingerprint","primary","status"],"type":"object"};
const schema37 = {"properties":{"message":{"type":"string"},"state":{"$ref":"#/$defs/NetworkState"}},"required":["state","message"],"type":"object"};
const schema38 = {"description":"Public connection progress; never contains invitations or private routing cards.","enum":["locked","local_only","invitation_required","connecting","connected","reconnecting","invitation_expired","unavailable"],"type":"string"};

function validate27(data, {instancePath="", parentData, parentDataProperty, rootData=data, dynamicAnchors={}}={}){
let vErrors = null;
let errors = 0;
const evaluated0 = validate27.evaluated;
if(evaluated0.dynamicProps){
evaluated0.props = undefined;
}
if(evaluated0.dynamicItems){
evaluated0.items = undefined;
}
if(errors === 0){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing0;
if(((data.state === undefined) && (missing0 = "state")) || ((data.message === undefined) && (missing0 = "message"))){
validate27.errors = [{instancePath,schemaPath:"#/required",keyword:"required",params:{missingProperty: missing0},message:"must have required property '"+missing0+"'"}];
return false;
}
else {
if(data.message !== undefined){
const _errs1 = errors;
if(typeof data.message !== "string"){
validate27.errors = [{instancePath:instancePath+"/message",schemaPath:"#/properties/message/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs1 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.state !== undefined){
let data1 = data.state;
const _errs3 = errors;
if(typeof data1 !== "string"){
validate27.errors = [{instancePath:instancePath+"/state",schemaPath:"#/$defs/NetworkState/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
if(!((((((((data1 === "locked") || (data1 === "local_only")) || (data1 === "invitation_required")) || (data1 === "connecting")) || (data1 === "connected")) || (data1 === "reconnecting")) || (data1 === "invitation_expired")) || (data1 === "unavailable"))){
validate27.errors = [{instancePath:instancePath+"/state",schemaPath:"#/$defs/NetworkState/enum",keyword:"enum",params:{allowedValues: schema38.enum},message:"must be equal to one of the allowed values"}];
return false;
}
var valid0 = _errs3 === errors;
}
else {
var valid0 = true;
}
}
}
}
else {
validate27.errors = [{instancePath,schemaPath:"#/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
validate27.errors = vErrors;
return errors === 0;
}
validate27.evaluated = {"props":{"message":true,"state":true},"dynamicProps":false,"dynamicItems":false};


function validate26(data, {instancePath="", parentData, parentDataProperty, rootData=data, dynamicAnchors={}}={}){
let vErrors = null;
let errors = 0;
const evaluated0 = validate26.evaluated;
if(evaluated0.dynamicProps){
evaluated0.props = undefined;
}
if(evaluated0.dynamicItems){
evaluated0.items = undefined;
}
if(errors === 0){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing0;
if((((((data.id === undefined) && (missing0 = "id")) || ((data.name === undefined) && (missing0 = "name"))) || ((data.fingerprint === undefined) && (missing0 = "fingerprint"))) || ((data.primary === undefined) && (missing0 = "primary"))) || ((data.status === undefined) && (missing0 = "status"))){
validate26.errors = [{instancePath,schemaPath:"#/required",keyword:"required",params:{missingProperty: missing0},message:"must have required property '"+missing0+"'"}];
return false;
}
else {
if(data.fingerprint !== undefined){
const _errs1 = errors;
if(typeof data.fingerprint !== "string"){
validate26.errors = [{instancePath:instancePath+"/fingerprint",schemaPath:"#/properties/fingerprint/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs1 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.id !== undefined){
const _errs3 = errors;
if(typeof data.id !== "string"){
validate26.errors = [{instancePath:instancePath+"/id",schemaPath:"#/properties/id/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs3 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.name !== undefined){
const _errs5 = errors;
if(typeof data.name !== "string"){
validate26.errors = [{instancePath:instancePath+"/name",schemaPath:"#/properties/name/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs5 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.primary !== undefined){
const _errs7 = errors;
if(typeof data.primary !== "boolean"){
validate26.errors = [{instancePath:instancePath+"/primary",schemaPath:"#/properties/primary/type",keyword:"type",params:{type: "boolean"},message:"must be boolean"}];
return false;
}
var valid0 = _errs7 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.status !== undefined){
const _errs9 = errors;
if(!(validate27(data.status, {instancePath:instancePath+"/status",parentData:data,parentDataProperty:"status",rootData,dynamicAnchors}))){
vErrors = vErrors === null ? validate27.errors : vErrors.concat(validate27.errors);
errors = vErrors.length;
}
var valid0 = _errs9 === errors;
}
else {
var valid0 = true;
}
}
}
}
}
}
}
else {
validate26.errors = [{instancePath,schemaPath:"#/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
validate26.errors = vErrors;
return errors === 0;
}
validate26.evaluated = {"props":{"fingerprint":true,"id":true,"name":true,"primary":true,"status":true},"dynamicProps":false,"dynamicItems":false};

const schema39 = {"properties":{"channel":{"type":["string","null"]},"expires":{"format":"uint64","minimum":0,"type":"integer"},"network":{"$ref":"#/$defs/JoinedNetwork"},"newNetwork":{"type":"boolean"}},"required":["network","newNetwork","expires"],"type":"object"};

function validate30(data, {instancePath="", parentData, parentDataProperty, rootData=data, dynamicAnchors={}}={}){
let vErrors = null;
let errors = 0;
const evaluated0 = validate30.evaluated;
if(evaluated0.dynamicProps){
evaluated0.props = undefined;
}
if(evaluated0.dynamicItems){
evaluated0.items = undefined;
}
if(errors === 0){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing0;
if((((data.network === undefined) && (missing0 = "network")) || ((data.newNetwork === undefined) && (missing0 = "newNetwork"))) || ((data.expires === undefined) && (missing0 = "expires"))){
validate30.errors = [{instancePath,schemaPath:"#/required",keyword:"required",params:{missingProperty: missing0},message:"must have required property '"+missing0+"'"}];
return false;
}
else {
if(data.channel !== undefined){
let data0 = data.channel;
const _errs1 = errors;
if((typeof data0 !== "string") && (data0 !== null)){
validate30.errors = [{instancePath:instancePath+"/channel",schemaPath:"#/properties/channel/type",keyword:"type",params:{type: schema39.properties.channel.type},message:"must be string,null"}];
return false;
}
var valid0 = _errs1 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.expires !== undefined){
let data1 = data.expires;
const _errs3 = errors;
if(!(((typeof data1 == "number") && (!(data1 % 1) && !isNaN(data1))) && (isFinite(data1)))){
validate30.errors = [{instancePath:instancePath+"/expires",schemaPath:"#/properties/expires/type",keyword:"type",params:{type: "integer"},message:"must be integer"}];
return false;
}
if(errors === _errs3){
if((typeof data1 == "number") && (isFinite(data1))){
if(data1 < 0 || isNaN(data1)){
validate30.errors = [{instancePath:instancePath+"/expires",schemaPath:"#/properties/expires/minimum",keyword:"minimum",params:{comparison: ">=", limit: 0},message:"must be >= 0"}];
return false;
}
}
}
var valid0 = _errs3 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.network !== undefined){
const _errs5 = errors;
if(!(validate26(data.network, {instancePath:instancePath+"/network",parentData:data,parentDataProperty:"network",rootData,dynamicAnchors}))){
vErrors = vErrors === null ? validate26.errors : vErrors.concat(validate26.errors);
errors = vErrors.length;
}
var valid0 = _errs5 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.newNetwork !== undefined){
const _errs6 = errors;
if(typeof data.newNetwork !== "boolean"){
validate30.errors = [{instancePath:instancePath+"/newNetwork",schemaPath:"#/properties/newNetwork/type",keyword:"type",params:{type: "boolean"},message:"must be boolean"}];
return false;
}
var valid0 = _errs6 === errors;
}
else {
var valid0 = true;
}
}
}
}
}
}
else {
validate30.errors = [{instancePath,schemaPath:"#/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
validate30.errors = vErrors;
return errors === 0;
}
validate30.evaluated = {"props":{"channel":true,"expires":true,"network":true,"newNetwork":true},"dynamicProps":false,"dynamicItems":false};

const schema40 = {"oneOf":[{"properties":{"kind":{"const":"networks","type":"string"},"response":{"$ref":"#"}},"required":["kind","response"],"type":"object"},{"properties":{"kind":{"const":"files","type":"string"},"snapshot":{"$ref":"#/$defs/FileSnapshot"}},"required":["kind","snapshot"],"type":"object"},{"properties":{"kind":{"const":"network_status","type":"string"},"status":{"$ref":"#/$defs/NetworkStatus"}},"required":["kind","status"],"type":"object"},{"properties":{"instance":{"$ref":"#/$defs/InstanceInfo"},"kind":{"const":"instance","type":"string"}},"required":["kind","instance"],"type":"object"},{"properties":{"kind":{"const":"snapshot","type":"string"},"snapshot":{"$ref":"#/$defs/Snapshot"}},"required":["kind","snapshot"],"type":"object"},{"properties":{"kind":{"const":"history","type":"string"},"page":{"$ref":"#/$defs/HistoryPage"}},"required":["kind","page"],"type":"object"},{"properties":{"items":{"items":{"$ref":"#/$defs/Completion"},"type":"array"},"kind":{"const":"completed","type":"string"}},"required":["kind","items"],"type":"object"},{"properties":{"commands":{"items":{"$ref":"#/$defs/CommandSpec"},"type":"array"},"kind":{"const":"catalogue","type":"string"}},"required":["kind","commands"],"type":"object"},{"properties":{"conversations":{"items":{"$ref":"#/$defs/Conversation"},"type":"array"},"kind":{"const":"projection","type":"string"},"revision":{"type":"string"}},"required":["kind","conversations","revision"],"type":"object"},{"properties":{"conversation":{"type":["string","null"]},"kind":{"const":"output","type":"string"},"output":{"$ref":"#/$defs/CommandOutput"}},"required":["kind","output"],"type":"object"},{"properties":{"conversation":{"type":["string","null"]},"kind":{"const":"applied","type":"string"},"notice":{"type":["string","null"]}},"required":["kind"],"type":"object"},{"properties":{"kind":{"const":"changed","type":"string"},"revision":{"type":"string"}},"required":["kind","revision"],"type":"object"},{"properties":{"code":{"type":"string"},"kind":{"const":"error","type":"string"},"message":{"type":"string"}},"required":["kind","code","message"],"type":"object"}]};
const schema44 = {"properties":{"archiveExists":{"type":"boolean"},"bootId":{"type":"string"},"capabilities":{"items":{"type":"string"},"type":"array"},"id":{"type":"string"},"label":{"type":"string"},"locked":{"type":"boolean"},"profileExists":{"type":"boolean"},"protocolLocked":{"type":"boolean"},"safetyNumber":{"type":"string"}},"required":["id","label","bootId","locked","protocolLocked","profileExists","archiveExists","safetyNumber","capabilities"],"type":"object"};
const schema63 = {"properties":{"description":{"type":"string"},"text":{"type":"string"}},"required":["text","description"],"type":"object"};
const schema48 = {"properties":{"available":{"type":"boolean"},"capability":{"type":["string","null"]},"description":{"type":"string"},"name":{"type":"string"},"scope":{"type":"string"},"usage":{"type":"string"}},"required":["name","usage","description","scope","available"],"type":"object"};
const root0 = {validate: validate25};
const schema41 = {"additionalProperties":false,"properties":{"files":{"items":{"$ref":"#/$defs/FileInfo"},"type":"array"},"quota_bytes":{"type":"string"},"retention_days":{"format":"uint16","maximum":65535,"minimum":0,"type":"integer"},"used_bytes":{"type":"string"}},"required":["files","quota_bytes","used_bytes","retention_days"],"type":"object"};
const schema42 = {"additionalProperties":false,"properties":{"aliases":{"default":null,"items":{"type":"string"},"type":["array","null"]},"completed_by":{"format":"uint16","maximum":65535,"minimum":0,"type":"integer"},"conversation":{"type":"string"},"error":{"type":["string","null"]},"id":{"type":"string"},"name":{"type":"string"},"size_bytes":{"type":"string"},"sources":{"format":"uint16","maximum":65535,"minimum":0,"type":"integer"},"state":{"$ref":"#/$defs/FileState"},"verified_bytes":{"type":"string"},"verified_sources":{"default":0,"description":"Peers contributing verified pieces since this process opened the cache.","format":"uint16","maximum":65535,"minimum":0,"type":"integer"}},"required":["id","conversation","name","size_bytes","verified_bytes","state","sources","completed_by"],"type":"object"};
const schema43 = {"enum":["offered","importing","downloading","waiting_for_peers","paused","complete","failed","cancelled"],"type":"string"};
const func1 = Object.prototype.hasOwnProperty;

function validate35(data, {instancePath="", parentData, parentDataProperty, rootData=data, dynamicAnchors={}}={}){
let vErrors = null;
let errors = 0;
const evaluated0 = validate35.evaluated;
if(evaluated0.dynamicProps){
evaluated0.props = undefined;
}
if(evaluated0.dynamicItems){
evaluated0.items = undefined;
}
if(errors === 0){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing0;
if(((((((((data.id === undefined) && (missing0 = "id")) || ((data.conversation === undefined) && (missing0 = "conversation"))) || ((data.name === undefined) && (missing0 = "name"))) || ((data.size_bytes === undefined) && (missing0 = "size_bytes"))) || ((data.verified_bytes === undefined) && (missing0 = "verified_bytes"))) || ((data.state === undefined) && (missing0 = "state"))) || ((data.sources === undefined) && (missing0 = "sources"))) || ((data.completed_by === undefined) && (missing0 = "completed_by"))){
validate35.errors = [{instancePath,schemaPath:"#/required",keyword:"required",params:{missingProperty: missing0},message:"must have required property '"+missing0+"'"}];
return false;
}
else {
const _errs1 = errors;
for(const key0 in data){
if(!(func1.call(schema42.properties, key0))){
validate35.errors = [{instancePath,schemaPath:"#/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key0},message:"must NOT have additional properties"}];
return false;
break;
}
}
if(_errs1 === errors){
if(data.aliases !== undefined){
let data0 = data.aliases;
const _errs2 = errors;
if((!(Array.isArray(data0))) && (data0 !== null)){
validate35.errors = [{instancePath:instancePath+"/aliases",schemaPath:"#/properties/aliases/type",keyword:"type",params:{type: schema42.properties.aliases.type},message:"must be array,null"}];
return false;
}
if(errors === _errs2){
if(Array.isArray(data0)){
var valid1 = true;
const len0 = data0.length;
for(let i0=0; i0<len0; i0++){
const _errs4 = errors;
if(typeof data0[i0] !== "string"){
validate35.errors = [{instancePath:instancePath+"/aliases/" + i0,schemaPath:"#/properties/aliases/items/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid1 = _errs4 === errors;
if(!valid1){
break;
}
}
}
}
var valid0 = _errs2 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.completed_by !== undefined){
let data2 = data.completed_by;
const _errs6 = errors;
if(!(((typeof data2 == "number") && (!(data2 % 1) && !isNaN(data2))) && (isFinite(data2)))){
validate35.errors = [{instancePath:instancePath+"/completed_by",schemaPath:"#/properties/completed_by/type",keyword:"type",params:{type: "integer"},message:"must be integer"}];
return false;
}
if(errors === _errs6){
if((typeof data2 == "number") && (isFinite(data2))){
if(data2 > 65535 || isNaN(data2)){
validate35.errors = [{instancePath:instancePath+"/completed_by",schemaPath:"#/properties/completed_by/maximum",keyword:"maximum",params:{comparison: "<=", limit: 65535},message:"must be <= 65535"}];
return false;
}
else {
if(data2 < 0 || isNaN(data2)){
validate35.errors = [{instancePath:instancePath+"/completed_by",schemaPath:"#/properties/completed_by/minimum",keyword:"minimum",params:{comparison: ">=", limit: 0},message:"must be >= 0"}];
return false;
}
}
}
}
var valid0 = _errs6 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.conversation !== undefined){
const _errs8 = errors;
if(typeof data.conversation !== "string"){
validate35.errors = [{instancePath:instancePath+"/conversation",schemaPath:"#/properties/conversation/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs8 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.error !== undefined){
let data4 = data.error;
const _errs10 = errors;
if((typeof data4 !== "string") && (data4 !== null)){
validate35.errors = [{instancePath:instancePath+"/error",schemaPath:"#/properties/error/type",keyword:"type",params:{type: schema42.properties.error.type},message:"must be string,null"}];
return false;
}
var valid0 = _errs10 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.id !== undefined){
const _errs12 = errors;
if(typeof data.id !== "string"){
validate35.errors = [{instancePath:instancePath+"/id",schemaPath:"#/properties/id/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs12 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.name !== undefined){
const _errs14 = errors;
if(typeof data.name !== "string"){
validate35.errors = [{instancePath:instancePath+"/name",schemaPath:"#/properties/name/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs14 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.size_bytes !== undefined){
const _errs16 = errors;
if(typeof data.size_bytes !== "string"){
validate35.errors = [{instancePath:instancePath+"/size_bytes",schemaPath:"#/properties/size_bytes/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs16 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.sources !== undefined){
let data8 = data.sources;
const _errs18 = errors;
if(!(((typeof data8 == "number") && (!(data8 % 1) && !isNaN(data8))) && (isFinite(data8)))){
validate35.errors = [{instancePath:instancePath+"/sources",schemaPath:"#/properties/sources/type",keyword:"type",params:{type: "integer"},message:"must be integer"}];
return false;
}
if(errors === _errs18){
if((typeof data8 == "number") && (isFinite(data8))){
if(data8 > 65535 || isNaN(data8)){
validate35.errors = [{instancePath:instancePath+"/sources",schemaPath:"#/properties/sources/maximum",keyword:"maximum",params:{comparison: "<=", limit: 65535},message:"must be <= 65535"}];
return false;
}
else {
if(data8 < 0 || isNaN(data8)){
validate35.errors = [{instancePath:instancePath+"/sources",schemaPath:"#/properties/sources/minimum",keyword:"minimum",params:{comparison: ">=", limit: 0},message:"must be >= 0"}];
return false;
}
}
}
}
var valid0 = _errs18 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.state !== undefined){
let data9 = data.state;
const _errs20 = errors;
if(typeof data9 !== "string"){
validate35.errors = [{instancePath:instancePath+"/state",schemaPath:"#/$defs/FileState/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
if(!((((((((data9 === "offered") || (data9 === "importing")) || (data9 === "downloading")) || (data9 === "waiting_for_peers")) || (data9 === "paused")) || (data9 === "complete")) || (data9 === "failed")) || (data9 === "cancelled"))){
validate35.errors = [{instancePath:instancePath+"/state",schemaPath:"#/$defs/FileState/enum",keyword:"enum",params:{allowedValues: schema43.enum},message:"must be equal to one of the allowed values"}];
return false;
}
var valid0 = _errs20 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.verified_bytes !== undefined){
const _errs23 = errors;
if(typeof data.verified_bytes !== "string"){
validate35.errors = [{instancePath:instancePath+"/verified_bytes",schemaPath:"#/properties/verified_bytes/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs23 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.verified_sources !== undefined){
let data11 = data.verified_sources;
const _errs25 = errors;
if(!(((typeof data11 == "number") && (!(data11 % 1) && !isNaN(data11))) && (isFinite(data11)))){
validate35.errors = [{instancePath:instancePath+"/verified_sources",schemaPath:"#/properties/verified_sources/type",keyword:"type",params:{type: "integer"},message:"must be integer"}];
return false;
}
if(errors === _errs25){
if((typeof data11 == "number") && (isFinite(data11))){
if(data11 > 65535 || isNaN(data11)){
validate35.errors = [{instancePath:instancePath+"/verified_sources",schemaPath:"#/properties/verified_sources/maximum",keyword:"maximum",params:{comparison: "<=", limit: 65535},message:"must be <= 65535"}];
return false;
}
else {
if(data11 < 0 || isNaN(data11)){
validate35.errors = [{instancePath:instancePath+"/verified_sources",schemaPath:"#/properties/verified_sources/minimum",keyword:"minimum",params:{comparison: ">=", limit: 0},message:"must be >= 0"}];
return false;
}
}
}
}
var valid0 = _errs25 === errors;
}
else {
var valid0 = true;
}
}
}
}
}
}
}
}
}
}
}
}
}
}
else {
validate35.errors = [{instancePath,schemaPath:"#/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
validate35.errors = vErrors;
return errors === 0;
}
validate35.evaluated = {"props":true,"dynamicProps":false,"dynamicItems":false};


function validate34(data, {instancePath="", parentData, parentDataProperty, rootData=data, dynamicAnchors={}}={}){
let vErrors = null;
let errors = 0;
const evaluated0 = validate34.evaluated;
if(evaluated0.dynamicProps){
evaluated0.props = undefined;
}
if(evaluated0.dynamicItems){
evaluated0.items = undefined;
}
if(errors === 0){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing0;
if(((((data.files === undefined) && (missing0 = "files")) || ((data.quota_bytes === undefined) && (missing0 = "quota_bytes"))) || ((data.used_bytes === undefined) && (missing0 = "used_bytes"))) || ((data.retention_days === undefined) && (missing0 = "retention_days"))){
validate34.errors = [{instancePath,schemaPath:"#/required",keyword:"required",params:{missingProperty: missing0},message:"must have required property '"+missing0+"'"}];
return false;
}
else {
const _errs1 = errors;
for(const key0 in data){
if(!((((key0 === "files") || (key0 === "quota_bytes")) || (key0 === "retention_days")) || (key0 === "used_bytes"))){
validate34.errors = [{instancePath,schemaPath:"#/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key0},message:"must NOT have additional properties"}];
return false;
break;
}
}
if(_errs1 === errors){
if(data.files !== undefined){
let data0 = data.files;
const _errs2 = errors;
if(errors === _errs2){
if(Array.isArray(data0)){
var valid1 = true;
const len0 = data0.length;
for(let i0=0; i0<len0; i0++){
const _errs4 = errors;
if(!(validate35(data0[i0], {instancePath:instancePath+"/files/" + i0,parentData:data0,parentDataProperty:i0,rootData,dynamicAnchors}))){
vErrors = vErrors === null ? validate35.errors : vErrors.concat(validate35.errors);
errors = vErrors.length;
}
var valid1 = _errs4 === errors;
if(!valid1){
break;
}
}
}
else {
validate34.errors = [{instancePath:instancePath+"/files",schemaPath:"#/properties/files/type",keyword:"type",params:{type: "array"},message:"must be array"}];
return false;
}
}
var valid0 = _errs2 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.quota_bytes !== undefined){
const _errs5 = errors;
if(typeof data.quota_bytes !== "string"){
validate34.errors = [{instancePath:instancePath+"/quota_bytes",schemaPath:"#/properties/quota_bytes/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs5 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.retention_days !== undefined){
let data3 = data.retention_days;
const _errs7 = errors;
if(!(((typeof data3 == "number") && (!(data3 % 1) && !isNaN(data3))) && (isFinite(data3)))){
validate34.errors = [{instancePath:instancePath+"/retention_days",schemaPath:"#/properties/retention_days/type",keyword:"type",params:{type: "integer"},message:"must be integer"}];
return false;
}
if(errors === _errs7){
if((typeof data3 == "number") && (isFinite(data3))){
if(data3 > 65535 || isNaN(data3)){
validate34.errors = [{instancePath:instancePath+"/retention_days",schemaPath:"#/properties/retention_days/maximum",keyword:"maximum",params:{comparison: "<=", limit: 65535},message:"must be <= 65535"}];
return false;
}
else {
if(data3 < 0 || isNaN(data3)){
validate34.errors = [{instancePath:instancePath+"/retention_days",schemaPath:"#/properties/retention_days/minimum",keyword:"minimum",params:{comparison: ">=", limit: 0},message:"must be >= 0"}];
return false;
}
}
}
}
var valid0 = _errs7 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.used_bytes !== undefined){
const _errs9 = errors;
if(typeof data.used_bytes !== "string"){
validate34.errors = [{instancePath:instancePath+"/used_bytes",schemaPath:"#/properties/used_bytes/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs9 === errors;
}
else {
var valid0 = true;
}
}
}
}
}
}
}
else {
validate34.errors = [{instancePath,schemaPath:"#/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
validate34.errors = vErrors;
return errors === 0;
}
validate34.evaluated = {"props":true,"dynamicProps":false,"dynamicItems":false};

const schema45 = {"properties":{"activity":{"default":null,"items":{"$ref":"#/$defs/Activity"},"type":["array","null"]},"commandHistory":{"items":{"type":"string"},"type":"array"},"conversations":{"items":{"$ref":"#/$defs/Conversation"},"type":"array"},"inputHistory":{"items":{"$ref":"#/$defs/InputHistoryEntry"},"type":"array"},"instance":{"$ref":"#/$defs/InstanceInfo"},"operations":{"default":null,"items":{"$ref":"#/$defs/OperationDetail"},"type":["array","null"]},"presenceEnabled":{"default":null,"type":["boolean","null"]},"providerErrors":{"default":[],"items":{"$ref":"#/$defs/ProviderStatus"},"type":"array"},"revision":{"type":"string"}},"required":["instance","revision","conversations","commandHistory","inputHistory"],"type":"object"};
const schema46 = {"description":"Authenticated state changes observed by this profile, retained before publication.","properties":{"conversation":{"type":"string"},"id":{"type":"string"},"kind":{"type":"string"},"text":{"type":"string"},"timestamp":{"format":"uint64","minimum":0,"type":"integer"}},"required":["id","conversation","kind","text","timestamp"],"type":"object"};
const schema51 = {"properties":{"conversation":{"type":["string","null"]},"text":{"type":"string"}},"required":["text"],"type":"object"};
const schema57 = {"properties":{"code":{"type":"string"},"id":{"type":"string"},"message":{"type":"string"},"retryable":{"type":"boolean"}},"required":["id","code","message","retryable"],"type":"object"};
const schema47 = {"properties":{"active":{"type":"boolean"},"channelId":{"type":"string"},"commands":{"default":[],"items":{"$ref":"#/$defs/CommandSpec"},"type":"array"},"directory":{"default":null,"type":["string","null"]},"id":{"type":"string"},"inputLimitBytes":{"default":12000,"format":"uint","minimum":0,"type":"integer"},"kind":{"$ref":"#/$defs/ConversationKind"},"lastMessageId":{"type":["string","null"]},"members":{"items":{"$ref":"#/$defs/Member"},"type":"array"},"name":{"type":"string"},"owner":{"type":"boolean"},"provider":{"default":null,"type":["string","null"]},"topic":{"type":"string"},"unread":{"format":"uint32","minimum":0,"type":"integer"},"visibility":{"default":null,"type":["string","null"]}},"required":["id","channelId","kind","name","topic","active","owner","members","unread"],"type":"object"};
const schema49 = {"enum":["channel","query","archive"],"type":"string"};
const schema50 = {"properties":{"capabilities":{"default":[],"items":{"type":"string"},"type":"array"},"id":{"type":"string"},"isSelf":{"type":"boolean"},"nickname":{"type":"string"},"recentlyActive":{"default":null,"type":["boolean","null"]}},"required":["id","nickname","isSelf"],"type":"object"};

function validate40(data, {instancePath="", parentData, parentDataProperty, rootData=data, dynamicAnchors={}}={}){
let vErrors = null;
let errors = 0;
const evaluated0 = validate40.evaluated;
if(evaluated0.dynamicProps){
evaluated0.props = undefined;
}
if(evaluated0.dynamicItems){
evaluated0.items = undefined;
}
if(errors === 0){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing0;
if((((((((((data.id === undefined) && (missing0 = "id")) || ((data.channelId === undefined) && (missing0 = "channelId"))) || ((data.kind === undefined) && (missing0 = "kind"))) || ((data.name === undefined) && (missing0 = "name"))) || ((data.topic === undefined) && (missing0 = "topic"))) || ((data.active === undefined) && (missing0 = "active"))) || ((data.owner === undefined) && (missing0 = "owner"))) || ((data.members === undefined) && (missing0 = "members"))) || ((data.unread === undefined) && (missing0 = "unread"))){
validate40.errors = [{instancePath,schemaPath:"#/required",keyword:"required",params:{missingProperty: missing0},message:"must have required property '"+missing0+"'"}];
return false;
}
else {
if(data.active !== undefined){
const _errs1 = errors;
if(typeof data.active !== "boolean"){
validate40.errors = [{instancePath:instancePath+"/active",schemaPath:"#/properties/active/type",keyword:"type",params:{type: "boolean"},message:"must be boolean"}];
return false;
}
var valid0 = _errs1 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.channelId !== undefined){
const _errs3 = errors;
if(typeof data.channelId !== "string"){
validate40.errors = [{instancePath:instancePath+"/channelId",schemaPath:"#/properties/channelId/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs3 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.commands !== undefined){
let data2 = data.commands;
const _errs5 = errors;
if(errors === _errs5){
if(Array.isArray(data2)){
var valid1 = true;
const len0 = data2.length;
for(let i0=0; i0<len0; i0++){
let data3 = data2[i0];
const _errs7 = errors;
const _errs8 = errors;
if(errors === _errs8){
if(data3 && typeof data3 == "object" && !Array.isArray(data3)){
let missing1;
if((((((data3.name === undefined) && (missing1 = "name")) || ((data3.usage === undefined) && (missing1 = "usage"))) || ((data3.description === undefined) && (missing1 = "description"))) || ((data3.scope === undefined) && (missing1 = "scope"))) || ((data3.available === undefined) && (missing1 = "available"))){
validate40.errors = [{instancePath:instancePath+"/commands/" + i0,schemaPath:"#/$defs/CommandSpec/required",keyword:"required",params:{missingProperty: missing1},message:"must have required property '"+missing1+"'"}];
return false;
}
else {
if(data3.available !== undefined){
const _errs10 = errors;
if(typeof data3.available !== "boolean"){
validate40.errors = [{instancePath:instancePath+"/commands/" + i0+"/available",schemaPath:"#/$defs/CommandSpec/properties/available/type",keyword:"type",params:{type: "boolean"},message:"must be boolean"}];
return false;
}
var valid3 = _errs10 === errors;
}
else {
var valid3 = true;
}
if(valid3){
if(data3.capability !== undefined){
let data5 = data3.capability;
const _errs12 = errors;
if((typeof data5 !== "string") && (data5 !== null)){
validate40.errors = [{instancePath:instancePath+"/commands/" + i0+"/capability",schemaPath:"#/$defs/CommandSpec/properties/capability/type",keyword:"type",params:{type: schema48.properties.capability.type},message:"must be string,null"}];
return false;
}
var valid3 = _errs12 === errors;
}
else {
var valid3 = true;
}
if(valid3){
if(data3.description !== undefined){
const _errs14 = errors;
if(typeof data3.description !== "string"){
validate40.errors = [{instancePath:instancePath+"/commands/" + i0+"/description",schemaPath:"#/$defs/CommandSpec/properties/description/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid3 = _errs14 === errors;
}
else {
var valid3 = true;
}
if(valid3){
if(data3.name !== undefined){
const _errs16 = errors;
if(typeof data3.name !== "string"){
validate40.errors = [{instancePath:instancePath+"/commands/" + i0+"/name",schemaPath:"#/$defs/CommandSpec/properties/name/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid3 = _errs16 === errors;
}
else {
var valid3 = true;
}
if(valid3){
if(data3.scope !== undefined){
const _errs18 = errors;
if(typeof data3.scope !== "string"){
validate40.errors = [{instancePath:instancePath+"/commands/" + i0+"/scope",schemaPath:"#/$defs/CommandSpec/properties/scope/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid3 = _errs18 === errors;
}
else {
var valid3 = true;
}
if(valid3){
if(data3.usage !== undefined){
const _errs20 = errors;
if(typeof data3.usage !== "string"){
validate40.errors = [{instancePath:instancePath+"/commands/" + i0+"/usage",schemaPath:"#/$defs/CommandSpec/properties/usage/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid3 = _errs20 === errors;
}
else {
var valid3 = true;
}
}
}
}
}
}
}
}
else {
validate40.errors = [{instancePath:instancePath+"/commands/" + i0,schemaPath:"#/$defs/CommandSpec/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
var valid1 = _errs7 === errors;
if(!valid1){
break;
}
}
}
else {
validate40.errors = [{instancePath:instancePath+"/commands",schemaPath:"#/properties/commands/type",keyword:"type",params:{type: "array"},message:"must be array"}];
return false;
}
}
var valid0 = _errs5 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.directory !== undefined){
let data10 = data.directory;
const _errs22 = errors;
if((typeof data10 !== "string") && (data10 !== null)){
validate40.errors = [{instancePath:instancePath+"/directory",schemaPath:"#/properties/directory/type",keyword:"type",params:{type: schema47.properties.directory.type},message:"must be string,null"}];
return false;
}
var valid0 = _errs22 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.id !== undefined){
const _errs24 = errors;
if(typeof data.id !== "string"){
validate40.errors = [{instancePath:instancePath+"/id",schemaPath:"#/properties/id/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs24 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.inputLimitBytes !== undefined){
let data12 = data.inputLimitBytes;
const _errs26 = errors;
if(!(((typeof data12 == "number") && (!(data12 % 1) && !isNaN(data12))) && (isFinite(data12)))){
validate40.errors = [{instancePath:instancePath+"/inputLimitBytes",schemaPath:"#/properties/inputLimitBytes/type",keyword:"type",params:{type: "integer"},message:"must be integer"}];
return false;
}
if(errors === _errs26){
if((typeof data12 == "number") && (isFinite(data12))){
if(data12 < 0 || isNaN(data12)){
validate40.errors = [{instancePath:instancePath+"/inputLimitBytes",schemaPath:"#/properties/inputLimitBytes/minimum",keyword:"minimum",params:{comparison: ">=", limit: 0},message:"must be >= 0"}];
return false;
}
}
}
var valid0 = _errs26 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.kind !== undefined){
let data13 = data.kind;
const _errs28 = errors;
if(typeof data13 !== "string"){
validate40.errors = [{instancePath:instancePath+"/kind",schemaPath:"#/$defs/ConversationKind/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
if(!(((data13 === "channel") || (data13 === "query")) || (data13 === "archive"))){
validate40.errors = [{instancePath:instancePath+"/kind",schemaPath:"#/$defs/ConversationKind/enum",keyword:"enum",params:{allowedValues: schema49.enum},message:"must be equal to one of the allowed values"}];
return false;
}
var valid0 = _errs28 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.lastMessageId !== undefined){
let data14 = data.lastMessageId;
const _errs31 = errors;
if((typeof data14 !== "string") && (data14 !== null)){
validate40.errors = [{instancePath:instancePath+"/lastMessageId",schemaPath:"#/properties/lastMessageId/type",keyword:"type",params:{type: schema47.properties.lastMessageId.type},message:"must be string,null"}];
return false;
}
var valid0 = _errs31 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.members !== undefined){
let data15 = data.members;
const _errs33 = errors;
if(errors === _errs33){
if(Array.isArray(data15)){
var valid5 = true;
const len1 = data15.length;
for(let i1=0; i1<len1; i1++){
let data16 = data15[i1];
const _errs35 = errors;
const _errs36 = errors;
if(errors === _errs36){
if(data16 && typeof data16 == "object" && !Array.isArray(data16)){
let missing2;
if((((data16.id === undefined) && (missing2 = "id")) || ((data16.nickname === undefined) && (missing2 = "nickname"))) || ((data16.isSelf === undefined) && (missing2 = "isSelf"))){
validate40.errors = [{instancePath:instancePath+"/members/" + i1,schemaPath:"#/$defs/Member/required",keyword:"required",params:{missingProperty: missing2},message:"must have required property '"+missing2+"'"}];
return false;
}
else {
if(data16.capabilities !== undefined){
let data17 = data16.capabilities;
const _errs38 = errors;
if(errors === _errs38){
if(Array.isArray(data17)){
var valid8 = true;
const len2 = data17.length;
for(let i2=0; i2<len2; i2++){
const _errs40 = errors;
if(typeof data17[i2] !== "string"){
validate40.errors = [{instancePath:instancePath+"/members/" + i1+"/capabilities/" + i2,schemaPath:"#/$defs/Member/properties/capabilities/items/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid8 = _errs40 === errors;
if(!valid8){
break;
}
}
}
else {
validate40.errors = [{instancePath:instancePath+"/members/" + i1+"/capabilities",schemaPath:"#/$defs/Member/properties/capabilities/type",keyword:"type",params:{type: "array"},message:"must be array"}];
return false;
}
}
var valid7 = _errs38 === errors;
}
else {
var valid7 = true;
}
if(valid7){
if(data16.id !== undefined){
const _errs42 = errors;
if(typeof data16.id !== "string"){
validate40.errors = [{instancePath:instancePath+"/members/" + i1+"/id",schemaPath:"#/$defs/Member/properties/id/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid7 = _errs42 === errors;
}
else {
var valid7 = true;
}
if(valid7){
if(data16.isSelf !== undefined){
const _errs44 = errors;
if(typeof data16.isSelf !== "boolean"){
validate40.errors = [{instancePath:instancePath+"/members/" + i1+"/isSelf",schemaPath:"#/$defs/Member/properties/isSelf/type",keyword:"type",params:{type: "boolean"},message:"must be boolean"}];
return false;
}
var valid7 = _errs44 === errors;
}
else {
var valid7 = true;
}
if(valid7){
if(data16.nickname !== undefined){
const _errs46 = errors;
if(typeof data16.nickname !== "string"){
validate40.errors = [{instancePath:instancePath+"/members/" + i1+"/nickname",schemaPath:"#/$defs/Member/properties/nickname/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid7 = _errs46 === errors;
}
else {
var valid7 = true;
}
if(valid7){
if(data16.recentlyActive !== undefined){
let data22 = data16.recentlyActive;
const _errs48 = errors;
if((typeof data22 !== "boolean") && (data22 !== null)){
validate40.errors = [{instancePath:instancePath+"/members/" + i1+"/recentlyActive",schemaPath:"#/$defs/Member/properties/recentlyActive/type",keyword:"type",params:{type: schema50.properties.recentlyActive.type},message:"must be boolean,null"}];
return false;
}
var valid7 = _errs48 === errors;
}
else {
var valid7 = true;
}
}
}
}
}
}
}
else {
validate40.errors = [{instancePath:instancePath+"/members/" + i1,schemaPath:"#/$defs/Member/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
var valid5 = _errs35 === errors;
if(!valid5){
break;
}
}
}
else {
validate40.errors = [{instancePath:instancePath+"/members",schemaPath:"#/properties/members/type",keyword:"type",params:{type: "array"},message:"must be array"}];
return false;
}
}
var valid0 = _errs33 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.name !== undefined){
const _errs50 = errors;
if(typeof data.name !== "string"){
validate40.errors = [{instancePath:instancePath+"/name",schemaPath:"#/properties/name/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs50 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.owner !== undefined){
const _errs52 = errors;
if(typeof data.owner !== "boolean"){
validate40.errors = [{instancePath:instancePath+"/owner",schemaPath:"#/properties/owner/type",keyword:"type",params:{type: "boolean"},message:"must be boolean"}];
return false;
}
var valid0 = _errs52 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.provider !== undefined){
let data25 = data.provider;
const _errs54 = errors;
if((typeof data25 !== "string") && (data25 !== null)){
validate40.errors = [{instancePath:instancePath+"/provider",schemaPath:"#/properties/provider/type",keyword:"type",params:{type: schema47.properties.provider.type},message:"must be string,null"}];
return false;
}
var valid0 = _errs54 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.topic !== undefined){
const _errs56 = errors;
if(typeof data.topic !== "string"){
validate40.errors = [{instancePath:instancePath+"/topic",schemaPath:"#/properties/topic/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs56 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.unread !== undefined){
let data27 = data.unread;
const _errs58 = errors;
if(!(((typeof data27 == "number") && (!(data27 % 1) && !isNaN(data27))) && (isFinite(data27)))){
validate40.errors = [{instancePath:instancePath+"/unread",schemaPath:"#/properties/unread/type",keyword:"type",params:{type: "integer"},message:"must be integer"}];
return false;
}
if(errors === _errs58){
if((typeof data27 == "number") && (isFinite(data27))){
if(data27 < 0 || isNaN(data27)){
validate40.errors = [{instancePath:instancePath+"/unread",schemaPath:"#/properties/unread/minimum",keyword:"minimum",params:{comparison: ">=", limit: 0},message:"must be >= 0"}];
return false;
}
}
}
var valid0 = _errs58 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.visibility !== undefined){
let data28 = data.visibility;
const _errs60 = errors;
if((typeof data28 !== "string") && (data28 !== null)){
validate40.errors = [{instancePath:instancePath+"/visibility",schemaPath:"#/properties/visibility/type",keyword:"type",params:{type: schema47.properties.visibility.type},message:"must be string,null"}];
return false;
}
var valid0 = _errs60 === errors;
}
else {
var valid0 = true;
}
}
}
}
}
}
}
}
}
}
}
}
}
}
}
}
}
else {
validate40.errors = [{instancePath,schemaPath:"#/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
validate40.errors = vErrors;
return errors === 0;
}
validate40.evaluated = {"props":{"active":true,"channelId":true,"commands":true,"directory":true,"id":true,"inputLimitBytes":true,"kind":true,"lastMessageId":true,"members":true,"name":true,"owner":true,"provider":true,"topic":true,"unread":true,"visibility":true},"dynamicProps":false,"dynamicItems":false};

const schema53 = {"description":"Safe metadata plus the protected result retained in the encrypted operation journal.","properties":{"action":{"type":"string"},"conversation":{"type":["string","null"]},"id":{"type":"string"},"instance":{"type":"string"},"message":{"type":["string","null"]},"network":{"default":null,"type":["string","null"]},"output":{"anyOf":[{"$ref":"#/$defs/CommandOutput"},{"type":"null"}]},"started":{"format":"uint64","minimum":0,"type":"integer"},"state":{"type":"string"}},"required":["id","instance","action","started","state"],"type":"object"};
const schema54 = {"oneOf":[{"properties":{"commands":{"items":{"$ref":"#/$defs/CommandSpec"},"type":"array"},"kind":{"const":"help","type":"string"}},"required":["kind","commands"],"type":"object"},{"properties":{"channels":{"items":{"$ref":"#/$defs/DirectoryEntry"},"type":"array"},"kind":{"const":"directory","type":"string"}},"required":["kind","channels"],"type":"object"},{"properties":{"channel":{"type":"string"},"expires":{"format":"uint64","minimum":0,"type":"integer"},"kind":{"const":"invitation","type":"string"},"link":{"type":"string"},"localOnly":{"default":false,"type":"boolean"}},"required":["kind","channel","link","expires"],"type":"object"},{"properties":{"kind":{"const":"text","type":"string"},"text":{"type":"string"},"title":{"type":"string"}},"required":["kind","title","text"],"type":"object"},{"properties":{"kind":{"const":"status","type":"string"},"text":{"type":"string"}},"required":["kind","text"],"type":"object"},{"properties":{"conversation":{"type":"string"},"kind":{"const":"close","type":"string"}},"required":["kind","conversation"],"type":"object"}]};
const schema56 = {"properties":{"conversation":{"type":["string","null"]},"joined":{"type":"boolean"},"name":{"type":"string"}},"required":["name","joined"],"type":"object"};

function validate43(data, {instancePath="", parentData, parentDataProperty, rootData=data, dynamicAnchors={}}={}){
let vErrors = null;
let errors = 0;
const evaluated0 = validate43.evaluated;
if(evaluated0.dynamicProps){
evaluated0.props = undefined;
}
if(evaluated0.dynamicItems){
evaluated0.items = undefined;
}
const _errs0 = errors;
let valid0 = false;
let passing0 = null;
const _errs1 = errors;
if(errors === _errs1){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing0;
if(((data.kind === undefined) && (missing0 = "kind")) || ((data.commands === undefined) && (missing0 = "commands"))){
const err0 = {instancePath,schemaPath:"#/oneOf/0/required",keyword:"required",params:{missingProperty: missing0},message:"must have required property '"+missing0+"'"};
if(vErrors === null){
vErrors = [err0];
}
else {
vErrors.push(err0);
}
errors++;
}
else {
if(data.commands !== undefined){
let data0 = data.commands;
const _errs3 = errors;
if(errors === _errs3){
if(Array.isArray(data0)){
var valid2 = true;
const len0 = data0.length;
for(let i0=0; i0<len0; i0++){
let data1 = data0[i0];
const _errs5 = errors;
const _errs6 = errors;
if(errors === _errs6){
if(data1 && typeof data1 == "object" && !Array.isArray(data1)){
let missing1;
if((((((data1.name === undefined) && (missing1 = "name")) || ((data1.usage === undefined) && (missing1 = "usage"))) || ((data1.description === undefined) && (missing1 = "description"))) || ((data1.scope === undefined) && (missing1 = "scope"))) || ((data1.available === undefined) && (missing1 = "available"))){
const err1 = {instancePath:instancePath+"/commands/" + i0,schemaPath:"#/$defs/CommandSpec/required",keyword:"required",params:{missingProperty: missing1},message:"must have required property '"+missing1+"'"};
if(vErrors === null){
vErrors = [err1];
}
else {
vErrors.push(err1);
}
errors++;
}
else {
if(data1.available !== undefined){
const _errs8 = errors;
if(typeof data1.available !== "boolean"){
const err2 = {instancePath:instancePath+"/commands/" + i0+"/available",schemaPath:"#/$defs/CommandSpec/properties/available/type",keyword:"type",params:{type: "boolean"},message:"must be boolean"};
if(vErrors === null){
vErrors = [err2];
}
else {
vErrors.push(err2);
}
errors++;
}
var valid4 = _errs8 === errors;
}
else {
var valid4 = true;
}
if(valid4){
if(data1.capability !== undefined){
let data3 = data1.capability;
const _errs10 = errors;
if((typeof data3 !== "string") && (data3 !== null)){
const err3 = {instancePath:instancePath+"/commands/" + i0+"/capability",schemaPath:"#/$defs/CommandSpec/properties/capability/type",keyword:"type",params:{type: schema48.properties.capability.type},message:"must be string,null"};
if(vErrors === null){
vErrors = [err3];
}
else {
vErrors.push(err3);
}
errors++;
}
var valid4 = _errs10 === errors;
}
else {
var valid4 = true;
}
if(valid4){
if(data1.description !== undefined){
const _errs12 = errors;
if(typeof data1.description !== "string"){
const err4 = {instancePath:instancePath+"/commands/" + i0+"/description",schemaPath:"#/$defs/CommandSpec/properties/description/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err4];
}
else {
vErrors.push(err4);
}
errors++;
}
var valid4 = _errs12 === errors;
}
else {
var valid4 = true;
}
if(valid4){
if(data1.name !== undefined){
const _errs14 = errors;
if(typeof data1.name !== "string"){
const err5 = {instancePath:instancePath+"/commands/" + i0+"/name",schemaPath:"#/$defs/CommandSpec/properties/name/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err5];
}
else {
vErrors.push(err5);
}
errors++;
}
var valid4 = _errs14 === errors;
}
else {
var valid4 = true;
}
if(valid4){
if(data1.scope !== undefined){
const _errs16 = errors;
if(typeof data1.scope !== "string"){
const err6 = {instancePath:instancePath+"/commands/" + i0+"/scope",schemaPath:"#/$defs/CommandSpec/properties/scope/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err6];
}
else {
vErrors.push(err6);
}
errors++;
}
var valid4 = _errs16 === errors;
}
else {
var valid4 = true;
}
if(valid4){
if(data1.usage !== undefined){
const _errs18 = errors;
if(typeof data1.usage !== "string"){
const err7 = {instancePath:instancePath+"/commands/" + i0+"/usage",schemaPath:"#/$defs/CommandSpec/properties/usage/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err7];
}
else {
vErrors.push(err7);
}
errors++;
}
var valid4 = _errs18 === errors;
}
else {
var valid4 = true;
}
}
}
}
}
}
}
}
else {
const err8 = {instancePath:instancePath+"/commands/" + i0,schemaPath:"#/$defs/CommandSpec/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err8];
}
else {
vErrors.push(err8);
}
errors++;
}
}
var valid2 = _errs5 === errors;
if(!valid2){
break;
}
}
}
else {
const err9 = {instancePath:instancePath+"/commands",schemaPath:"#/oneOf/0/properties/commands/type",keyword:"type",params:{type: "array"},message:"must be array"};
if(vErrors === null){
vErrors = [err9];
}
else {
vErrors.push(err9);
}
errors++;
}
}
var valid1 = _errs3 === errors;
}
else {
var valid1 = true;
}
if(valid1){
if(data.kind !== undefined){
let data8 = data.kind;
const _errs20 = errors;
if(typeof data8 !== "string"){
const err10 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/0/properties/kind/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err10];
}
else {
vErrors.push(err10);
}
errors++;
}
if("help" !== data8){
const err11 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/0/properties/kind/const",keyword:"const",params:{allowedValue: "help"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err11];
}
else {
vErrors.push(err11);
}
errors++;
}
var valid1 = _errs20 === errors;
}
else {
var valid1 = true;
}
}
}
}
else {
const err12 = {instancePath,schemaPath:"#/oneOf/0/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err12];
}
else {
vErrors.push(err12);
}
errors++;
}
}
var _valid0 = _errs1 === errors;
if(_valid0){
valid0 = true;
passing0 = 0;
var props0 = {};
props0.commands = true;
props0.kind = true;
}
const _errs22 = errors;
if(errors === _errs22){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing2;
if(((data.kind === undefined) && (missing2 = "kind")) || ((data.channels === undefined) && (missing2 = "channels"))){
const err13 = {instancePath,schemaPath:"#/oneOf/1/required",keyword:"required",params:{missingProperty: missing2},message:"must have required property '"+missing2+"'"};
if(vErrors === null){
vErrors = [err13];
}
else {
vErrors.push(err13);
}
errors++;
}
else {
if(data.channels !== undefined){
let data9 = data.channels;
const _errs24 = errors;
if(errors === _errs24){
if(Array.isArray(data9)){
var valid6 = true;
const len1 = data9.length;
for(let i1=0; i1<len1; i1++){
let data10 = data9[i1];
const _errs26 = errors;
const _errs27 = errors;
if(errors === _errs27){
if(data10 && typeof data10 == "object" && !Array.isArray(data10)){
let missing3;
if(((data10.name === undefined) && (missing3 = "name")) || ((data10.joined === undefined) && (missing3 = "joined"))){
const err14 = {instancePath:instancePath+"/channels/" + i1,schemaPath:"#/$defs/DirectoryEntry/required",keyword:"required",params:{missingProperty: missing3},message:"must have required property '"+missing3+"'"};
if(vErrors === null){
vErrors = [err14];
}
else {
vErrors.push(err14);
}
errors++;
}
else {
if(data10.conversation !== undefined){
let data11 = data10.conversation;
const _errs29 = errors;
if((typeof data11 !== "string") && (data11 !== null)){
const err15 = {instancePath:instancePath+"/channels/" + i1+"/conversation",schemaPath:"#/$defs/DirectoryEntry/properties/conversation/type",keyword:"type",params:{type: schema56.properties.conversation.type},message:"must be string,null"};
if(vErrors === null){
vErrors = [err15];
}
else {
vErrors.push(err15);
}
errors++;
}
var valid8 = _errs29 === errors;
}
else {
var valid8 = true;
}
if(valid8){
if(data10.joined !== undefined){
const _errs31 = errors;
if(typeof data10.joined !== "boolean"){
const err16 = {instancePath:instancePath+"/channels/" + i1+"/joined",schemaPath:"#/$defs/DirectoryEntry/properties/joined/type",keyword:"type",params:{type: "boolean"},message:"must be boolean"};
if(vErrors === null){
vErrors = [err16];
}
else {
vErrors.push(err16);
}
errors++;
}
var valid8 = _errs31 === errors;
}
else {
var valid8 = true;
}
if(valid8){
if(data10.name !== undefined){
const _errs33 = errors;
if(typeof data10.name !== "string"){
const err17 = {instancePath:instancePath+"/channels/" + i1+"/name",schemaPath:"#/$defs/DirectoryEntry/properties/name/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err17];
}
else {
vErrors.push(err17);
}
errors++;
}
var valid8 = _errs33 === errors;
}
else {
var valid8 = true;
}
}
}
}
}
else {
const err18 = {instancePath:instancePath+"/channels/" + i1,schemaPath:"#/$defs/DirectoryEntry/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err18];
}
else {
vErrors.push(err18);
}
errors++;
}
}
var valid6 = _errs26 === errors;
if(!valid6){
break;
}
}
}
else {
const err19 = {instancePath:instancePath+"/channels",schemaPath:"#/oneOf/1/properties/channels/type",keyword:"type",params:{type: "array"},message:"must be array"};
if(vErrors === null){
vErrors = [err19];
}
else {
vErrors.push(err19);
}
errors++;
}
}
var valid5 = _errs24 === errors;
}
else {
var valid5 = true;
}
if(valid5){
if(data.kind !== undefined){
let data14 = data.kind;
const _errs35 = errors;
if(typeof data14 !== "string"){
const err20 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/1/properties/kind/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err20];
}
else {
vErrors.push(err20);
}
errors++;
}
if("directory" !== data14){
const err21 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/1/properties/kind/const",keyword:"const",params:{allowedValue: "directory"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err21];
}
else {
vErrors.push(err21);
}
errors++;
}
var valid5 = _errs35 === errors;
}
else {
var valid5 = true;
}
}
}
}
else {
const err22 = {instancePath,schemaPath:"#/oneOf/1/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err22];
}
else {
vErrors.push(err22);
}
errors++;
}
}
var _valid0 = _errs22 === errors;
if(_valid0 && valid0){
valid0 = false;
passing0 = [passing0, 1];
}
else {
if(_valid0){
valid0 = true;
passing0 = 1;
if(props0 !== true){
props0 = props0 || {};
props0.channels = true;
props0.kind = true;
}
}
const _errs37 = errors;
if(errors === _errs37){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing4;
if(((((data.kind === undefined) && (missing4 = "kind")) || ((data.channel === undefined) && (missing4 = "channel"))) || ((data.link === undefined) && (missing4 = "link"))) || ((data.expires === undefined) && (missing4 = "expires"))){
const err23 = {instancePath,schemaPath:"#/oneOf/2/required",keyword:"required",params:{missingProperty: missing4},message:"must have required property '"+missing4+"'"};
if(vErrors === null){
vErrors = [err23];
}
else {
vErrors.push(err23);
}
errors++;
}
else {
if(data.channel !== undefined){
const _errs39 = errors;
if(typeof data.channel !== "string"){
const err24 = {instancePath:instancePath+"/channel",schemaPath:"#/oneOf/2/properties/channel/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err24];
}
else {
vErrors.push(err24);
}
errors++;
}
var valid9 = _errs39 === errors;
}
else {
var valid9 = true;
}
if(valid9){
if(data.expires !== undefined){
let data16 = data.expires;
const _errs41 = errors;
if(!(((typeof data16 == "number") && (!(data16 % 1) && !isNaN(data16))) && (isFinite(data16)))){
const err25 = {instancePath:instancePath+"/expires",schemaPath:"#/oneOf/2/properties/expires/type",keyword:"type",params:{type: "integer"},message:"must be integer"};
if(vErrors === null){
vErrors = [err25];
}
else {
vErrors.push(err25);
}
errors++;
}
if(errors === _errs41){
if((typeof data16 == "number") && (isFinite(data16))){
if(data16 < 0 || isNaN(data16)){
const err26 = {instancePath:instancePath+"/expires",schemaPath:"#/oneOf/2/properties/expires/minimum",keyword:"minimum",params:{comparison: ">=", limit: 0},message:"must be >= 0"};
if(vErrors === null){
vErrors = [err26];
}
else {
vErrors.push(err26);
}
errors++;
}
}
}
var valid9 = _errs41 === errors;
}
else {
var valid9 = true;
}
if(valid9){
if(data.kind !== undefined){
let data17 = data.kind;
const _errs43 = errors;
if(typeof data17 !== "string"){
const err27 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/2/properties/kind/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err27];
}
else {
vErrors.push(err27);
}
errors++;
}
if("invitation" !== data17){
const err28 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/2/properties/kind/const",keyword:"const",params:{allowedValue: "invitation"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err28];
}
else {
vErrors.push(err28);
}
errors++;
}
var valid9 = _errs43 === errors;
}
else {
var valid9 = true;
}
if(valid9){
if(data.link !== undefined){
const _errs45 = errors;
if(typeof data.link !== "string"){
const err29 = {instancePath:instancePath+"/link",schemaPath:"#/oneOf/2/properties/link/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err29];
}
else {
vErrors.push(err29);
}
errors++;
}
var valid9 = _errs45 === errors;
}
else {
var valid9 = true;
}
if(valid9){
if(data.localOnly !== undefined){
const _errs47 = errors;
if(typeof data.localOnly !== "boolean"){
const err30 = {instancePath:instancePath+"/localOnly",schemaPath:"#/oneOf/2/properties/localOnly/type",keyword:"type",params:{type: "boolean"},message:"must be boolean"};
if(vErrors === null){
vErrors = [err30];
}
else {
vErrors.push(err30);
}
errors++;
}
var valid9 = _errs47 === errors;
}
else {
var valid9 = true;
}
}
}
}
}
}
}
else {
const err31 = {instancePath,schemaPath:"#/oneOf/2/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err31];
}
else {
vErrors.push(err31);
}
errors++;
}
}
var _valid0 = _errs37 === errors;
if(_valid0 && valid0){
valid0 = false;
passing0 = [passing0, 2];
}
else {
if(_valid0){
valid0 = true;
passing0 = 2;
if(props0 !== true){
props0 = props0 || {};
props0.channel = true;
props0.expires = true;
props0.kind = true;
props0.link = true;
props0.localOnly = true;
}
}
const _errs49 = errors;
if(errors === _errs49){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing5;
if((((data.kind === undefined) && (missing5 = "kind")) || ((data.title === undefined) && (missing5 = "title"))) || ((data.text === undefined) && (missing5 = "text"))){
const err32 = {instancePath,schemaPath:"#/oneOf/3/required",keyword:"required",params:{missingProperty: missing5},message:"must have required property '"+missing5+"'"};
if(vErrors === null){
vErrors = [err32];
}
else {
vErrors.push(err32);
}
errors++;
}
else {
if(data.kind !== undefined){
let data20 = data.kind;
const _errs51 = errors;
if(typeof data20 !== "string"){
const err33 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/3/properties/kind/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err33];
}
else {
vErrors.push(err33);
}
errors++;
}
if("text" !== data20){
const err34 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/3/properties/kind/const",keyword:"const",params:{allowedValue: "text"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err34];
}
else {
vErrors.push(err34);
}
errors++;
}
var valid10 = _errs51 === errors;
}
else {
var valid10 = true;
}
if(valid10){
if(data.text !== undefined){
const _errs53 = errors;
if(typeof data.text !== "string"){
const err35 = {instancePath:instancePath+"/text",schemaPath:"#/oneOf/3/properties/text/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err35];
}
else {
vErrors.push(err35);
}
errors++;
}
var valid10 = _errs53 === errors;
}
else {
var valid10 = true;
}
if(valid10){
if(data.title !== undefined){
const _errs55 = errors;
if(typeof data.title !== "string"){
const err36 = {instancePath:instancePath+"/title",schemaPath:"#/oneOf/3/properties/title/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err36];
}
else {
vErrors.push(err36);
}
errors++;
}
var valid10 = _errs55 === errors;
}
else {
var valid10 = true;
}
}
}
}
}
else {
const err37 = {instancePath,schemaPath:"#/oneOf/3/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err37];
}
else {
vErrors.push(err37);
}
errors++;
}
}
var _valid0 = _errs49 === errors;
if(_valid0 && valid0){
valid0 = false;
passing0 = [passing0, 3];
}
else {
if(_valid0){
valid0 = true;
passing0 = 3;
if(props0 !== true){
props0 = props0 || {};
props0.kind = true;
props0.text = true;
props0.title = true;
}
}
const _errs57 = errors;
if(errors === _errs57){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing6;
if(((data.kind === undefined) && (missing6 = "kind")) || ((data.text === undefined) && (missing6 = "text"))){
const err38 = {instancePath,schemaPath:"#/oneOf/4/required",keyword:"required",params:{missingProperty: missing6},message:"must have required property '"+missing6+"'"};
if(vErrors === null){
vErrors = [err38];
}
else {
vErrors.push(err38);
}
errors++;
}
else {
if(data.kind !== undefined){
let data23 = data.kind;
const _errs59 = errors;
if(typeof data23 !== "string"){
const err39 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/4/properties/kind/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err39];
}
else {
vErrors.push(err39);
}
errors++;
}
if("status" !== data23){
const err40 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/4/properties/kind/const",keyword:"const",params:{allowedValue: "status"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err40];
}
else {
vErrors.push(err40);
}
errors++;
}
var valid11 = _errs59 === errors;
}
else {
var valid11 = true;
}
if(valid11){
if(data.text !== undefined){
const _errs61 = errors;
if(typeof data.text !== "string"){
const err41 = {instancePath:instancePath+"/text",schemaPath:"#/oneOf/4/properties/text/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err41];
}
else {
vErrors.push(err41);
}
errors++;
}
var valid11 = _errs61 === errors;
}
else {
var valid11 = true;
}
}
}
}
else {
const err42 = {instancePath,schemaPath:"#/oneOf/4/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err42];
}
else {
vErrors.push(err42);
}
errors++;
}
}
var _valid0 = _errs57 === errors;
if(_valid0 && valid0){
valid0 = false;
passing0 = [passing0, 4];
}
else {
if(_valid0){
valid0 = true;
passing0 = 4;
if(props0 !== true){
props0 = props0 || {};
props0.kind = true;
props0.text = true;
}
}
const _errs63 = errors;
if(errors === _errs63){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing7;
if(((data.kind === undefined) && (missing7 = "kind")) || ((data.conversation === undefined) && (missing7 = "conversation"))){
const err43 = {instancePath,schemaPath:"#/oneOf/5/required",keyword:"required",params:{missingProperty: missing7},message:"must have required property '"+missing7+"'"};
if(vErrors === null){
vErrors = [err43];
}
else {
vErrors.push(err43);
}
errors++;
}
else {
if(data.conversation !== undefined){
const _errs65 = errors;
if(typeof data.conversation !== "string"){
const err44 = {instancePath:instancePath+"/conversation",schemaPath:"#/oneOf/5/properties/conversation/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err44];
}
else {
vErrors.push(err44);
}
errors++;
}
var valid12 = _errs65 === errors;
}
else {
var valid12 = true;
}
if(valid12){
if(data.kind !== undefined){
let data26 = data.kind;
const _errs67 = errors;
if(typeof data26 !== "string"){
const err45 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/5/properties/kind/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err45];
}
else {
vErrors.push(err45);
}
errors++;
}
if("close" !== data26){
const err46 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/5/properties/kind/const",keyword:"const",params:{allowedValue: "close"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err46];
}
else {
vErrors.push(err46);
}
errors++;
}
var valid12 = _errs67 === errors;
}
else {
var valid12 = true;
}
}
}
}
else {
const err47 = {instancePath,schemaPath:"#/oneOf/5/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err47];
}
else {
vErrors.push(err47);
}
errors++;
}
}
var _valid0 = _errs63 === errors;
if(_valid0 && valid0){
valid0 = false;
passing0 = [passing0, 5];
}
else {
if(_valid0){
valid0 = true;
passing0 = 5;
if(props0 !== true){
props0 = props0 || {};
props0.conversation = true;
props0.kind = true;
}
}
}
}
}
}
}
if(!valid0){
const err48 = {instancePath,schemaPath:"#/oneOf",keyword:"oneOf",params:{passingSchemas: passing0},message:"must match exactly one schema in oneOf"};
if(vErrors === null){
vErrors = [err48];
}
else {
vErrors.push(err48);
}
errors++;
validate43.errors = vErrors;
return false;
}
else {
errors = _errs0;
if(vErrors !== null){
if(_errs0){
vErrors.length = _errs0;
}
else {
vErrors = null;
}
}
}
validate43.errors = vErrors;
evaluated0.props = props0;
return errors === 0;
}
validate43.evaluated = {"dynamicProps":true,"dynamicItems":false};


function validate42(data, {instancePath="", parentData, parentDataProperty, rootData=data, dynamicAnchors={}}={}){
let vErrors = null;
let errors = 0;
const evaluated0 = validate42.evaluated;
if(evaluated0.dynamicProps){
evaluated0.props = undefined;
}
if(evaluated0.dynamicItems){
evaluated0.items = undefined;
}
if(errors === 0){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing0;
if((((((data.id === undefined) && (missing0 = "id")) || ((data.instance === undefined) && (missing0 = "instance"))) || ((data.action === undefined) && (missing0 = "action"))) || ((data.started === undefined) && (missing0 = "started"))) || ((data.state === undefined) && (missing0 = "state"))){
validate42.errors = [{instancePath,schemaPath:"#/required",keyword:"required",params:{missingProperty: missing0},message:"must have required property '"+missing0+"'"}];
return false;
}
else {
if(data.action !== undefined){
const _errs1 = errors;
if(typeof data.action !== "string"){
validate42.errors = [{instancePath:instancePath+"/action",schemaPath:"#/properties/action/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs1 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.conversation !== undefined){
let data1 = data.conversation;
const _errs3 = errors;
if((typeof data1 !== "string") && (data1 !== null)){
validate42.errors = [{instancePath:instancePath+"/conversation",schemaPath:"#/properties/conversation/type",keyword:"type",params:{type: schema53.properties.conversation.type},message:"must be string,null"}];
return false;
}
var valid0 = _errs3 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.id !== undefined){
const _errs5 = errors;
if(typeof data.id !== "string"){
validate42.errors = [{instancePath:instancePath+"/id",schemaPath:"#/properties/id/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs5 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.instance !== undefined){
const _errs7 = errors;
if(typeof data.instance !== "string"){
validate42.errors = [{instancePath:instancePath+"/instance",schemaPath:"#/properties/instance/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs7 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.message !== undefined){
let data4 = data.message;
const _errs9 = errors;
if((typeof data4 !== "string") && (data4 !== null)){
validate42.errors = [{instancePath:instancePath+"/message",schemaPath:"#/properties/message/type",keyword:"type",params:{type: schema53.properties.message.type},message:"must be string,null"}];
return false;
}
var valid0 = _errs9 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.network !== undefined){
let data5 = data.network;
const _errs11 = errors;
if((typeof data5 !== "string") && (data5 !== null)){
validate42.errors = [{instancePath:instancePath+"/network",schemaPath:"#/properties/network/type",keyword:"type",params:{type: schema53.properties.network.type},message:"must be string,null"}];
return false;
}
var valid0 = _errs11 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.output !== undefined){
let data6 = data.output;
const _errs13 = errors;
const _errs14 = errors;
let valid1 = false;
const _errs15 = errors;
if(!(validate43(data6, {instancePath:instancePath+"/output",parentData:data,parentDataProperty:"output",rootData,dynamicAnchors}))){
vErrors = vErrors === null ? validate43.errors : vErrors.concat(validate43.errors);
errors = vErrors.length;
}
var _valid0 = _errs15 === errors;
valid1 = valid1 || _valid0;
const _errs16 = errors;
if(data6 !== null){
const err0 = {instancePath:instancePath+"/output",schemaPath:"#/properties/output/anyOf/1/type",keyword:"type",params:{type: "null"},message:"must be null"};
if(vErrors === null){
vErrors = [err0];
}
else {
vErrors.push(err0);
}
errors++;
}
var _valid0 = _errs16 === errors;
valid1 = valid1 || _valid0;
if(!valid1){
const err1 = {instancePath:instancePath+"/output",schemaPath:"#/properties/output/anyOf",keyword:"anyOf",params:{},message:"must match a schema in anyOf"};
if(vErrors === null){
vErrors = [err1];
}
else {
vErrors.push(err1);
}
errors++;
validate42.errors = vErrors;
return false;
}
else {
errors = _errs14;
if(vErrors !== null){
if(_errs14){
vErrors.length = _errs14;
}
else {
vErrors = null;
}
}
}
var valid0 = _errs13 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.started !== undefined){
let data7 = data.started;
const _errs18 = errors;
if(!(((typeof data7 == "number") && (!(data7 % 1) && !isNaN(data7))) && (isFinite(data7)))){
validate42.errors = [{instancePath:instancePath+"/started",schemaPath:"#/properties/started/type",keyword:"type",params:{type: "integer"},message:"must be integer"}];
return false;
}
if(errors === _errs18){
if((typeof data7 == "number") && (isFinite(data7))){
if(data7 < 0 || isNaN(data7)){
validate42.errors = [{instancePath:instancePath+"/started",schemaPath:"#/properties/started/minimum",keyword:"minimum",params:{comparison: ">=", limit: 0},message:"must be >= 0"}];
return false;
}
}
}
var valid0 = _errs18 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.state !== undefined){
const _errs20 = errors;
if(typeof data.state !== "string"){
validate42.errors = [{instancePath:instancePath+"/state",schemaPath:"#/properties/state/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs20 === errors;
}
else {
var valid0 = true;
}
}
}
}
}
}
}
}
}
}
}
else {
validate42.errors = [{instancePath,schemaPath:"#/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
validate42.errors = vErrors;
return errors === 0;
}
validate42.evaluated = {"props":{"action":true,"conversation":true,"id":true,"instance":true,"message":true,"network":true,"output":true,"started":true,"state":true},"dynamicProps":false,"dynamicItems":false};


function validate39(data, {instancePath="", parentData, parentDataProperty, rootData=data, dynamicAnchors={}}={}){
let vErrors = null;
let errors = 0;
const evaluated0 = validate39.evaluated;
if(evaluated0.dynamicProps){
evaluated0.props = undefined;
}
if(evaluated0.dynamicItems){
evaluated0.items = undefined;
}
if(errors === 0){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing0;
if((((((data.instance === undefined) && (missing0 = "instance")) || ((data.revision === undefined) && (missing0 = "revision"))) || ((data.conversations === undefined) && (missing0 = "conversations"))) || ((data.commandHistory === undefined) && (missing0 = "commandHistory"))) || ((data.inputHistory === undefined) && (missing0 = "inputHistory"))){
validate39.errors = [{instancePath,schemaPath:"#/required",keyword:"required",params:{missingProperty: missing0},message:"must have required property '"+missing0+"'"}];
return false;
}
else {
if(data.activity !== undefined){
let data0 = data.activity;
const _errs1 = errors;
if((!(Array.isArray(data0))) && (data0 !== null)){
validate39.errors = [{instancePath:instancePath+"/activity",schemaPath:"#/properties/activity/type",keyword:"type",params:{type: schema45.properties.activity.type},message:"must be array,null"}];
return false;
}
if(errors === _errs1){
if(Array.isArray(data0)){
var valid1 = true;
const len0 = data0.length;
for(let i0=0; i0<len0; i0++){
let data1 = data0[i0];
const _errs3 = errors;
const _errs4 = errors;
if(errors === _errs4){
if(data1 && typeof data1 == "object" && !Array.isArray(data1)){
let missing1;
if((((((data1.id === undefined) && (missing1 = "id")) || ((data1.conversation === undefined) && (missing1 = "conversation"))) || ((data1.kind === undefined) && (missing1 = "kind"))) || ((data1.text === undefined) && (missing1 = "text"))) || ((data1.timestamp === undefined) && (missing1 = "timestamp"))){
validate39.errors = [{instancePath:instancePath+"/activity/" + i0,schemaPath:"#/$defs/Activity/required",keyword:"required",params:{missingProperty: missing1},message:"must have required property '"+missing1+"'"}];
return false;
}
else {
if(data1.conversation !== undefined){
const _errs6 = errors;
if(typeof data1.conversation !== "string"){
validate39.errors = [{instancePath:instancePath+"/activity/" + i0+"/conversation",schemaPath:"#/$defs/Activity/properties/conversation/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid3 = _errs6 === errors;
}
else {
var valid3 = true;
}
if(valid3){
if(data1.id !== undefined){
const _errs8 = errors;
if(typeof data1.id !== "string"){
validate39.errors = [{instancePath:instancePath+"/activity/" + i0+"/id",schemaPath:"#/$defs/Activity/properties/id/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid3 = _errs8 === errors;
}
else {
var valid3 = true;
}
if(valid3){
if(data1.kind !== undefined){
const _errs10 = errors;
if(typeof data1.kind !== "string"){
validate39.errors = [{instancePath:instancePath+"/activity/" + i0+"/kind",schemaPath:"#/$defs/Activity/properties/kind/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid3 = _errs10 === errors;
}
else {
var valid3 = true;
}
if(valid3){
if(data1.text !== undefined){
const _errs12 = errors;
if(typeof data1.text !== "string"){
validate39.errors = [{instancePath:instancePath+"/activity/" + i0+"/text",schemaPath:"#/$defs/Activity/properties/text/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid3 = _errs12 === errors;
}
else {
var valid3 = true;
}
if(valid3){
if(data1.timestamp !== undefined){
let data6 = data1.timestamp;
const _errs14 = errors;
if(!(((typeof data6 == "number") && (!(data6 % 1) && !isNaN(data6))) && (isFinite(data6)))){
validate39.errors = [{instancePath:instancePath+"/activity/" + i0+"/timestamp",schemaPath:"#/$defs/Activity/properties/timestamp/type",keyword:"type",params:{type: "integer"},message:"must be integer"}];
return false;
}
if(errors === _errs14){
if((typeof data6 == "number") && (isFinite(data6))){
if(data6 < 0 || isNaN(data6)){
validate39.errors = [{instancePath:instancePath+"/activity/" + i0+"/timestamp",schemaPath:"#/$defs/Activity/properties/timestamp/minimum",keyword:"minimum",params:{comparison: ">=", limit: 0},message:"must be >= 0"}];
return false;
}
}
}
var valid3 = _errs14 === errors;
}
else {
var valid3 = true;
}
}
}
}
}
}
}
else {
validate39.errors = [{instancePath:instancePath+"/activity/" + i0,schemaPath:"#/$defs/Activity/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
var valid1 = _errs3 === errors;
if(!valid1){
break;
}
}
}
}
var valid0 = _errs1 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.commandHistory !== undefined){
let data7 = data.commandHistory;
const _errs16 = errors;
if(errors === _errs16){
if(Array.isArray(data7)){
var valid4 = true;
const len1 = data7.length;
for(let i1=0; i1<len1; i1++){
const _errs18 = errors;
if(typeof data7[i1] !== "string"){
validate39.errors = [{instancePath:instancePath+"/commandHistory/" + i1,schemaPath:"#/properties/commandHistory/items/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid4 = _errs18 === errors;
if(!valid4){
break;
}
}
}
else {
validate39.errors = [{instancePath:instancePath+"/commandHistory",schemaPath:"#/properties/commandHistory/type",keyword:"type",params:{type: "array"},message:"must be array"}];
return false;
}
}
var valid0 = _errs16 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.conversations !== undefined){
let data9 = data.conversations;
const _errs20 = errors;
if(errors === _errs20){
if(Array.isArray(data9)){
var valid5 = true;
const len2 = data9.length;
for(let i2=0; i2<len2; i2++){
const _errs22 = errors;
if(!(validate40(data9[i2], {instancePath:instancePath+"/conversations/" + i2,parentData:data9,parentDataProperty:i2,rootData,dynamicAnchors}))){
vErrors = vErrors === null ? validate40.errors : vErrors.concat(validate40.errors);
errors = vErrors.length;
}
var valid5 = _errs22 === errors;
if(!valid5){
break;
}
}
}
else {
validate39.errors = [{instancePath:instancePath+"/conversations",schemaPath:"#/properties/conversations/type",keyword:"type",params:{type: "array"},message:"must be array"}];
return false;
}
}
var valid0 = _errs20 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.inputHistory !== undefined){
let data11 = data.inputHistory;
const _errs23 = errors;
if(errors === _errs23){
if(Array.isArray(data11)){
var valid6 = true;
const len3 = data11.length;
for(let i3=0; i3<len3; i3++){
let data12 = data11[i3];
const _errs25 = errors;
const _errs26 = errors;
if(errors === _errs26){
if(data12 && typeof data12 == "object" && !Array.isArray(data12)){
let missing2;
if((data12.text === undefined) && (missing2 = "text")){
validate39.errors = [{instancePath:instancePath+"/inputHistory/" + i3,schemaPath:"#/$defs/InputHistoryEntry/required",keyword:"required",params:{missingProperty: missing2},message:"must have required property '"+missing2+"'"}];
return false;
}
else {
if(data12.conversation !== undefined){
let data13 = data12.conversation;
const _errs28 = errors;
if((typeof data13 !== "string") && (data13 !== null)){
validate39.errors = [{instancePath:instancePath+"/inputHistory/" + i3+"/conversation",schemaPath:"#/$defs/InputHistoryEntry/properties/conversation/type",keyword:"type",params:{type: schema51.properties.conversation.type},message:"must be string,null"}];
return false;
}
var valid8 = _errs28 === errors;
}
else {
var valid8 = true;
}
if(valid8){
if(data12.text !== undefined){
const _errs30 = errors;
if(typeof data12.text !== "string"){
validate39.errors = [{instancePath:instancePath+"/inputHistory/" + i3+"/text",schemaPath:"#/$defs/InputHistoryEntry/properties/text/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid8 = _errs30 === errors;
}
else {
var valid8 = true;
}
}
}
}
else {
validate39.errors = [{instancePath:instancePath+"/inputHistory/" + i3,schemaPath:"#/$defs/InputHistoryEntry/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
var valid6 = _errs25 === errors;
if(!valid6){
break;
}
}
}
else {
validate39.errors = [{instancePath:instancePath+"/inputHistory",schemaPath:"#/properties/inputHistory/type",keyword:"type",params:{type: "array"},message:"must be array"}];
return false;
}
}
var valid0 = _errs23 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.instance !== undefined){
let data15 = data.instance;
const _errs32 = errors;
const _errs33 = errors;
if(errors === _errs33){
if(data15 && typeof data15 == "object" && !Array.isArray(data15)){
let missing3;
if((((((((((data15.id === undefined) && (missing3 = "id")) || ((data15.label === undefined) && (missing3 = "label"))) || ((data15.bootId === undefined) && (missing3 = "bootId"))) || ((data15.locked === undefined) && (missing3 = "locked"))) || ((data15.protocolLocked === undefined) && (missing3 = "protocolLocked"))) || ((data15.profileExists === undefined) && (missing3 = "profileExists"))) || ((data15.archiveExists === undefined) && (missing3 = "archiveExists"))) || ((data15.safetyNumber === undefined) && (missing3 = "safetyNumber"))) || ((data15.capabilities === undefined) && (missing3 = "capabilities"))){
validate39.errors = [{instancePath:instancePath+"/instance",schemaPath:"#/$defs/InstanceInfo/required",keyword:"required",params:{missingProperty: missing3},message:"must have required property '"+missing3+"'"}];
return false;
}
else {
if(data15.archiveExists !== undefined){
const _errs35 = errors;
if(typeof data15.archiveExists !== "boolean"){
validate39.errors = [{instancePath:instancePath+"/instance/archiveExists",schemaPath:"#/$defs/InstanceInfo/properties/archiveExists/type",keyword:"type",params:{type: "boolean"},message:"must be boolean"}];
return false;
}
var valid10 = _errs35 === errors;
}
else {
var valid10 = true;
}
if(valid10){
if(data15.bootId !== undefined){
const _errs37 = errors;
if(typeof data15.bootId !== "string"){
validate39.errors = [{instancePath:instancePath+"/instance/bootId",schemaPath:"#/$defs/InstanceInfo/properties/bootId/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid10 = _errs37 === errors;
}
else {
var valid10 = true;
}
if(valid10){
if(data15.capabilities !== undefined){
let data18 = data15.capabilities;
const _errs39 = errors;
if(errors === _errs39){
if(Array.isArray(data18)){
var valid11 = true;
const len4 = data18.length;
for(let i4=0; i4<len4; i4++){
const _errs41 = errors;
if(typeof data18[i4] !== "string"){
validate39.errors = [{instancePath:instancePath+"/instance/capabilities/" + i4,schemaPath:"#/$defs/InstanceInfo/properties/capabilities/items/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid11 = _errs41 === errors;
if(!valid11){
break;
}
}
}
else {
validate39.errors = [{instancePath:instancePath+"/instance/capabilities",schemaPath:"#/$defs/InstanceInfo/properties/capabilities/type",keyword:"type",params:{type: "array"},message:"must be array"}];
return false;
}
}
var valid10 = _errs39 === errors;
}
else {
var valid10 = true;
}
if(valid10){
if(data15.id !== undefined){
const _errs43 = errors;
if(typeof data15.id !== "string"){
validate39.errors = [{instancePath:instancePath+"/instance/id",schemaPath:"#/$defs/InstanceInfo/properties/id/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid10 = _errs43 === errors;
}
else {
var valid10 = true;
}
if(valid10){
if(data15.label !== undefined){
const _errs45 = errors;
if(typeof data15.label !== "string"){
validate39.errors = [{instancePath:instancePath+"/instance/label",schemaPath:"#/$defs/InstanceInfo/properties/label/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid10 = _errs45 === errors;
}
else {
var valid10 = true;
}
if(valid10){
if(data15.locked !== undefined){
const _errs47 = errors;
if(typeof data15.locked !== "boolean"){
validate39.errors = [{instancePath:instancePath+"/instance/locked",schemaPath:"#/$defs/InstanceInfo/properties/locked/type",keyword:"type",params:{type: "boolean"},message:"must be boolean"}];
return false;
}
var valid10 = _errs47 === errors;
}
else {
var valid10 = true;
}
if(valid10){
if(data15.profileExists !== undefined){
const _errs49 = errors;
if(typeof data15.profileExists !== "boolean"){
validate39.errors = [{instancePath:instancePath+"/instance/profileExists",schemaPath:"#/$defs/InstanceInfo/properties/profileExists/type",keyword:"type",params:{type: "boolean"},message:"must be boolean"}];
return false;
}
var valid10 = _errs49 === errors;
}
else {
var valid10 = true;
}
if(valid10){
if(data15.protocolLocked !== undefined){
const _errs51 = errors;
if(typeof data15.protocolLocked !== "boolean"){
validate39.errors = [{instancePath:instancePath+"/instance/protocolLocked",schemaPath:"#/$defs/InstanceInfo/properties/protocolLocked/type",keyword:"type",params:{type: "boolean"},message:"must be boolean"}];
return false;
}
var valid10 = _errs51 === errors;
}
else {
var valid10 = true;
}
if(valid10){
if(data15.safetyNumber !== undefined){
const _errs53 = errors;
if(typeof data15.safetyNumber !== "string"){
validate39.errors = [{instancePath:instancePath+"/instance/safetyNumber",schemaPath:"#/$defs/InstanceInfo/properties/safetyNumber/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid10 = _errs53 === errors;
}
else {
var valid10 = true;
}
}
}
}
}
}
}
}
}
}
}
else {
validate39.errors = [{instancePath:instancePath+"/instance",schemaPath:"#/$defs/InstanceInfo/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
var valid0 = _errs32 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.operations !== undefined){
let data26 = data.operations;
const _errs55 = errors;
if((!(Array.isArray(data26))) && (data26 !== null)){
validate39.errors = [{instancePath:instancePath+"/operations",schemaPath:"#/properties/operations/type",keyword:"type",params:{type: schema45.properties.operations.type},message:"must be array,null"}];
return false;
}
if(errors === _errs55){
if(Array.isArray(data26)){
var valid12 = true;
const len5 = data26.length;
for(let i5=0; i5<len5; i5++){
const _errs57 = errors;
if(!(validate42(data26[i5], {instancePath:instancePath+"/operations/" + i5,parentData:data26,parentDataProperty:i5,rootData,dynamicAnchors}))){
vErrors = vErrors === null ? validate42.errors : vErrors.concat(validate42.errors);
errors = vErrors.length;
}
var valid12 = _errs57 === errors;
if(!valid12){
break;
}
}
}
}
var valid0 = _errs55 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.presenceEnabled !== undefined){
let data28 = data.presenceEnabled;
const _errs58 = errors;
if((typeof data28 !== "boolean") && (data28 !== null)){
validate39.errors = [{instancePath:instancePath+"/presenceEnabled",schemaPath:"#/properties/presenceEnabled/type",keyword:"type",params:{type: schema45.properties.presenceEnabled.type},message:"must be boolean,null"}];
return false;
}
var valid0 = _errs58 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.providerErrors !== undefined){
let data29 = data.providerErrors;
const _errs60 = errors;
if(errors === _errs60){
if(Array.isArray(data29)){
var valid13 = true;
const len6 = data29.length;
for(let i6=0; i6<len6; i6++){
let data30 = data29[i6];
const _errs62 = errors;
const _errs63 = errors;
if(errors === _errs63){
if(data30 && typeof data30 == "object" && !Array.isArray(data30)){
let missing4;
if(((((data30.id === undefined) && (missing4 = "id")) || ((data30.code === undefined) && (missing4 = "code"))) || ((data30.message === undefined) && (missing4 = "message"))) || ((data30.retryable === undefined) && (missing4 = "retryable"))){
validate39.errors = [{instancePath:instancePath+"/providerErrors/" + i6,schemaPath:"#/$defs/ProviderStatus/required",keyword:"required",params:{missingProperty: missing4},message:"must have required property '"+missing4+"'"}];
return false;
}
else {
if(data30.code !== undefined){
const _errs65 = errors;
if(typeof data30.code !== "string"){
validate39.errors = [{instancePath:instancePath+"/providerErrors/" + i6+"/code",schemaPath:"#/$defs/ProviderStatus/properties/code/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid15 = _errs65 === errors;
}
else {
var valid15 = true;
}
if(valid15){
if(data30.id !== undefined){
const _errs67 = errors;
if(typeof data30.id !== "string"){
validate39.errors = [{instancePath:instancePath+"/providerErrors/" + i6+"/id",schemaPath:"#/$defs/ProviderStatus/properties/id/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid15 = _errs67 === errors;
}
else {
var valid15 = true;
}
if(valid15){
if(data30.message !== undefined){
const _errs69 = errors;
if(typeof data30.message !== "string"){
validate39.errors = [{instancePath:instancePath+"/providerErrors/" + i6+"/message",schemaPath:"#/$defs/ProviderStatus/properties/message/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid15 = _errs69 === errors;
}
else {
var valid15 = true;
}
if(valid15){
if(data30.retryable !== undefined){
const _errs71 = errors;
if(typeof data30.retryable !== "boolean"){
validate39.errors = [{instancePath:instancePath+"/providerErrors/" + i6+"/retryable",schemaPath:"#/$defs/ProviderStatus/properties/retryable/type",keyword:"type",params:{type: "boolean"},message:"must be boolean"}];
return false;
}
var valid15 = _errs71 === errors;
}
else {
var valid15 = true;
}
}
}
}
}
}
else {
validate39.errors = [{instancePath:instancePath+"/providerErrors/" + i6,schemaPath:"#/$defs/ProviderStatus/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
var valid13 = _errs62 === errors;
if(!valid13){
break;
}
}
}
else {
validate39.errors = [{instancePath:instancePath+"/providerErrors",schemaPath:"#/properties/providerErrors/type",keyword:"type",params:{type: "array"},message:"must be array"}];
return false;
}
}
var valid0 = _errs60 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.revision !== undefined){
const _errs73 = errors;
if(typeof data.revision !== "string"){
validate39.errors = [{instancePath:instancePath+"/revision",schemaPath:"#/properties/revision/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs73 === errors;
}
else {
var valid0 = true;
}
}
}
}
}
}
}
}
}
}
}
else {
validate39.errors = [{instancePath,schemaPath:"#/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
validate39.errors = vErrors;
return errors === 0;
}
validate39.evaluated = {"props":{"activity":true,"commandHistory":true,"conversations":true,"inputHistory":true,"instance":true,"operations":true,"presenceEnabled":true,"providerErrors":true,"revision":true},"dynamicProps":false,"dynamicItems":false};

const schema58 = {"properties":{"before":{"type":["string","null"]},"messages":{"items":{"$ref":"#/$defs/Message"},"type":"array"}},"required":["messages"],"type":"object"};
const schema59 = {"properties":{"body":{"type":"string"},"conversationId":{"type":"string"},"delivery":{"anyOf":[{"$ref":"#/$defs/Delivery"},{"type":"null"}],"description":"Delivered is an authenticated recipient acknowledgement, never a read receipt."},"id":{"type":"string"},"memberId":{"type":["string","null"]},"mine":{"type":"boolean"},"nickname":{"type":"string"},"operationId":{"default":null,"type":["string","null"]},"result":{"anyOf":[{"$ref":"#/$defs/ActionResult"},{"type":"null"}],"default":null},"timestamp":{"format":"uint64","minimum":0,"type":"integer"}},"required":["id","conversationId","nickname","body","timestamp","mine"],"type":"object"};
const schema60 = {"enum":["local_accepted","delivered"],"type":"string"};
const schema61 = {"properties":{"artifacts":{"items":{"$ref":"#/$defs/Artifact"},"type":"array"},"details":{"items":{"type":"string"},"type":"array"},"id":{"type":"string"},"messageId":{"default":null,"type":["string","null"]},"outputBase64":{"description":"Exact signed bytes, base64 encoded; views decode only for display.","type":["string","null"]},"state":{"type":"string"},"stderr":{"type":"boolean"}},"required":["id","state","stderr","details","artifacts"],"type":"object"};
const schema62 = {"properties":{"name":{"type":"string"},"url":{"type":"string"}},"required":["name","url"],"type":"object"};

function validate49(data, {instancePath="", parentData, parentDataProperty, rootData=data, dynamicAnchors={}}={}){
let vErrors = null;
let errors = 0;
const evaluated0 = validate49.evaluated;
if(evaluated0.dynamicProps){
evaluated0.props = undefined;
}
if(evaluated0.dynamicItems){
evaluated0.items = undefined;
}
if(errors === 0){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing0;
if((((((data.id === undefined) && (missing0 = "id")) || ((data.state === undefined) && (missing0 = "state"))) || ((data.stderr === undefined) && (missing0 = "stderr"))) || ((data.details === undefined) && (missing0 = "details"))) || ((data.artifacts === undefined) && (missing0 = "artifacts"))){
validate49.errors = [{instancePath,schemaPath:"#/required",keyword:"required",params:{missingProperty: missing0},message:"must have required property '"+missing0+"'"}];
return false;
}
else {
if(data.artifacts !== undefined){
let data0 = data.artifacts;
const _errs1 = errors;
if(errors === _errs1){
if(Array.isArray(data0)){
var valid1 = true;
const len0 = data0.length;
for(let i0=0; i0<len0; i0++){
let data1 = data0[i0];
const _errs3 = errors;
const _errs4 = errors;
if(errors === _errs4){
if(data1 && typeof data1 == "object" && !Array.isArray(data1)){
let missing1;
if(((data1.name === undefined) && (missing1 = "name")) || ((data1.url === undefined) && (missing1 = "url"))){
validate49.errors = [{instancePath:instancePath+"/artifacts/" + i0,schemaPath:"#/$defs/Artifact/required",keyword:"required",params:{missingProperty: missing1},message:"must have required property '"+missing1+"'"}];
return false;
}
else {
if(data1.name !== undefined){
const _errs6 = errors;
if(typeof data1.name !== "string"){
validate49.errors = [{instancePath:instancePath+"/artifacts/" + i0+"/name",schemaPath:"#/$defs/Artifact/properties/name/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid3 = _errs6 === errors;
}
else {
var valid3 = true;
}
if(valid3){
if(data1.url !== undefined){
const _errs8 = errors;
if(typeof data1.url !== "string"){
validate49.errors = [{instancePath:instancePath+"/artifacts/" + i0+"/url",schemaPath:"#/$defs/Artifact/properties/url/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid3 = _errs8 === errors;
}
else {
var valid3 = true;
}
}
}
}
else {
validate49.errors = [{instancePath:instancePath+"/artifacts/" + i0,schemaPath:"#/$defs/Artifact/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
var valid1 = _errs3 === errors;
if(!valid1){
break;
}
}
}
else {
validate49.errors = [{instancePath:instancePath+"/artifacts",schemaPath:"#/properties/artifacts/type",keyword:"type",params:{type: "array"},message:"must be array"}];
return false;
}
}
var valid0 = _errs1 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.details !== undefined){
let data4 = data.details;
const _errs10 = errors;
if(errors === _errs10){
if(Array.isArray(data4)){
var valid4 = true;
const len1 = data4.length;
for(let i1=0; i1<len1; i1++){
const _errs12 = errors;
if(typeof data4[i1] !== "string"){
validate49.errors = [{instancePath:instancePath+"/details/" + i1,schemaPath:"#/properties/details/items/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid4 = _errs12 === errors;
if(!valid4){
break;
}
}
}
else {
validate49.errors = [{instancePath:instancePath+"/details",schemaPath:"#/properties/details/type",keyword:"type",params:{type: "array"},message:"must be array"}];
return false;
}
}
var valid0 = _errs10 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.id !== undefined){
const _errs14 = errors;
if(typeof data.id !== "string"){
validate49.errors = [{instancePath:instancePath+"/id",schemaPath:"#/properties/id/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs14 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.messageId !== undefined){
let data7 = data.messageId;
const _errs16 = errors;
if((typeof data7 !== "string") && (data7 !== null)){
validate49.errors = [{instancePath:instancePath+"/messageId",schemaPath:"#/properties/messageId/type",keyword:"type",params:{type: schema61.properties.messageId.type},message:"must be string,null"}];
return false;
}
var valid0 = _errs16 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.outputBase64 !== undefined){
let data8 = data.outputBase64;
const _errs18 = errors;
if((typeof data8 !== "string") && (data8 !== null)){
validate49.errors = [{instancePath:instancePath+"/outputBase64",schemaPath:"#/properties/outputBase64/type",keyword:"type",params:{type: schema61.properties.outputBase64.type},message:"must be string,null"}];
return false;
}
var valid0 = _errs18 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.state !== undefined){
const _errs20 = errors;
if(typeof data.state !== "string"){
validate49.errors = [{instancePath:instancePath+"/state",schemaPath:"#/properties/state/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs20 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.stderr !== undefined){
const _errs22 = errors;
if(typeof data.stderr !== "boolean"){
validate49.errors = [{instancePath:instancePath+"/stderr",schemaPath:"#/properties/stderr/type",keyword:"type",params:{type: "boolean"},message:"must be boolean"}];
return false;
}
var valid0 = _errs22 === errors;
}
else {
var valid0 = true;
}
}
}
}
}
}
}
}
}
else {
validate49.errors = [{instancePath,schemaPath:"#/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
validate49.errors = vErrors;
return errors === 0;
}
validate49.evaluated = {"props":{"artifacts":true,"details":true,"id":true,"messageId":true,"outputBase64":true,"state":true,"stderr":true},"dynamicProps":false,"dynamicItems":false};


function validate48(data, {instancePath="", parentData, parentDataProperty, rootData=data, dynamicAnchors={}}={}){
let vErrors = null;
let errors = 0;
const evaluated0 = validate48.evaluated;
if(evaluated0.dynamicProps){
evaluated0.props = undefined;
}
if(evaluated0.dynamicItems){
evaluated0.items = undefined;
}
if(errors === 0){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing0;
if(((((((data.id === undefined) && (missing0 = "id")) || ((data.conversationId === undefined) && (missing0 = "conversationId"))) || ((data.nickname === undefined) && (missing0 = "nickname"))) || ((data.body === undefined) && (missing0 = "body"))) || ((data.timestamp === undefined) && (missing0 = "timestamp"))) || ((data.mine === undefined) && (missing0 = "mine"))){
validate48.errors = [{instancePath,schemaPath:"#/required",keyword:"required",params:{missingProperty: missing0},message:"must have required property '"+missing0+"'"}];
return false;
}
else {
if(data.body !== undefined){
const _errs1 = errors;
if(typeof data.body !== "string"){
validate48.errors = [{instancePath:instancePath+"/body",schemaPath:"#/properties/body/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs1 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.conversationId !== undefined){
const _errs3 = errors;
if(typeof data.conversationId !== "string"){
validate48.errors = [{instancePath:instancePath+"/conversationId",schemaPath:"#/properties/conversationId/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs3 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.delivery !== undefined){
let data2 = data.delivery;
const _errs5 = errors;
const _errs6 = errors;
let valid1 = false;
const _errs7 = errors;
if(typeof data2 !== "string"){
const err0 = {instancePath:instancePath+"/delivery",schemaPath:"#/$defs/Delivery/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err0];
}
else {
vErrors.push(err0);
}
errors++;
}
if(!((data2 === "local_accepted") || (data2 === "delivered"))){
const err1 = {instancePath:instancePath+"/delivery",schemaPath:"#/$defs/Delivery/enum",keyword:"enum",params:{allowedValues: schema60.enum},message:"must be equal to one of the allowed values"};
if(vErrors === null){
vErrors = [err1];
}
else {
vErrors.push(err1);
}
errors++;
}
var _valid0 = _errs7 === errors;
valid1 = valid1 || _valid0;
const _errs10 = errors;
if(data2 !== null){
const err2 = {instancePath:instancePath+"/delivery",schemaPath:"#/properties/delivery/anyOf/1/type",keyword:"type",params:{type: "null"},message:"must be null"};
if(vErrors === null){
vErrors = [err2];
}
else {
vErrors.push(err2);
}
errors++;
}
var _valid0 = _errs10 === errors;
valid1 = valid1 || _valid0;
if(!valid1){
const err3 = {instancePath:instancePath+"/delivery",schemaPath:"#/properties/delivery/anyOf",keyword:"anyOf",params:{},message:"must match a schema in anyOf"};
if(vErrors === null){
vErrors = [err3];
}
else {
vErrors.push(err3);
}
errors++;
validate48.errors = vErrors;
return false;
}
else {
errors = _errs6;
if(vErrors !== null){
if(_errs6){
vErrors.length = _errs6;
}
else {
vErrors = null;
}
}
}
var valid0 = _errs5 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.id !== undefined){
const _errs12 = errors;
if(typeof data.id !== "string"){
validate48.errors = [{instancePath:instancePath+"/id",schemaPath:"#/properties/id/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs12 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.memberId !== undefined){
let data4 = data.memberId;
const _errs14 = errors;
if((typeof data4 !== "string") && (data4 !== null)){
validate48.errors = [{instancePath:instancePath+"/memberId",schemaPath:"#/properties/memberId/type",keyword:"type",params:{type: schema59.properties.memberId.type},message:"must be string,null"}];
return false;
}
var valid0 = _errs14 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.mine !== undefined){
const _errs16 = errors;
if(typeof data.mine !== "boolean"){
validate48.errors = [{instancePath:instancePath+"/mine",schemaPath:"#/properties/mine/type",keyword:"type",params:{type: "boolean"},message:"must be boolean"}];
return false;
}
var valid0 = _errs16 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.nickname !== undefined){
const _errs18 = errors;
if(typeof data.nickname !== "string"){
validate48.errors = [{instancePath:instancePath+"/nickname",schemaPath:"#/properties/nickname/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs18 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.operationId !== undefined){
let data7 = data.operationId;
const _errs20 = errors;
if((typeof data7 !== "string") && (data7 !== null)){
validate48.errors = [{instancePath:instancePath+"/operationId",schemaPath:"#/properties/operationId/type",keyword:"type",params:{type: schema59.properties.operationId.type},message:"must be string,null"}];
return false;
}
var valid0 = _errs20 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.result !== undefined){
let data8 = data.result;
const _errs22 = errors;
const _errs23 = errors;
let valid3 = false;
const _errs24 = errors;
if(!(validate49(data8, {instancePath:instancePath+"/result",parentData:data,parentDataProperty:"result",rootData,dynamicAnchors}))){
vErrors = vErrors === null ? validate49.errors : vErrors.concat(validate49.errors);
errors = vErrors.length;
}
var _valid1 = _errs24 === errors;
valid3 = valid3 || _valid1;
if(_valid1){
var props0 = {};
props0.artifacts = true;
props0.details = true;
props0.id = true;
props0.messageId = true;
props0.outputBase64 = true;
props0.state = true;
props0.stderr = true;
}
const _errs25 = errors;
if(data8 !== null){
const err4 = {instancePath:instancePath+"/result",schemaPath:"#/properties/result/anyOf/1/type",keyword:"type",params:{type: "null"},message:"must be null"};
if(vErrors === null){
vErrors = [err4];
}
else {
vErrors.push(err4);
}
errors++;
}
var _valid1 = _errs25 === errors;
valid3 = valid3 || _valid1;
if(!valid3){
const err5 = {instancePath:instancePath+"/result",schemaPath:"#/properties/result/anyOf",keyword:"anyOf",params:{},message:"must match a schema in anyOf"};
if(vErrors === null){
vErrors = [err5];
}
else {
vErrors.push(err5);
}
errors++;
validate48.errors = vErrors;
return false;
}
else {
errors = _errs23;
if(vErrors !== null){
if(_errs23){
vErrors.length = _errs23;
}
else {
vErrors = null;
}
}
}
var valid0 = _errs22 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.timestamp !== undefined){
let data9 = data.timestamp;
const _errs27 = errors;
if(!(((typeof data9 == "number") && (!(data9 % 1) && !isNaN(data9))) && (isFinite(data9)))){
validate48.errors = [{instancePath:instancePath+"/timestamp",schemaPath:"#/properties/timestamp/type",keyword:"type",params:{type: "integer"},message:"must be integer"}];
return false;
}
if(errors === _errs27){
if((typeof data9 == "number") && (isFinite(data9))){
if(data9 < 0 || isNaN(data9)){
validate48.errors = [{instancePath:instancePath+"/timestamp",schemaPath:"#/properties/timestamp/minimum",keyword:"minimum",params:{comparison: ">=", limit: 0},message:"must be >= 0"}];
return false;
}
}
}
var valid0 = _errs27 === errors;
}
else {
var valid0 = true;
}
}
}
}
}
}
}
}
}
}
}
}
else {
validate48.errors = [{instancePath,schemaPath:"#/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
validate48.errors = vErrors;
return errors === 0;
}
validate48.evaluated = {"props":{"body":true,"conversationId":true,"delivery":true,"id":true,"memberId":true,"mine":true,"nickname":true,"operationId":true,"result":true,"timestamp":true},"dynamicProps":false,"dynamicItems":false};


function validate47(data, {instancePath="", parentData, parentDataProperty, rootData=data, dynamicAnchors={}}={}){
let vErrors = null;
let errors = 0;
const evaluated0 = validate47.evaluated;
if(evaluated0.dynamicProps){
evaluated0.props = undefined;
}
if(evaluated0.dynamicItems){
evaluated0.items = undefined;
}
if(errors === 0){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing0;
if((data.messages === undefined) && (missing0 = "messages")){
validate47.errors = [{instancePath,schemaPath:"#/required",keyword:"required",params:{missingProperty: missing0},message:"must have required property '"+missing0+"'"}];
return false;
}
else {
if(data.before !== undefined){
let data0 = data.before;
const _errs1 = errors;
if((typeof data0 !== "string") && (data0 !== null)){
validate47.errors = [{instancePath:instancePath+"/before",schemaPath:"#/properties/before/type",keyword:"type",params:{type: schema58.properties.before.type},message:"must be string,null"}];
return false;
}
var valid0 = _errs1 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.messages !== undefined){
let data1 = data.messages;
const _errs3 = errors;
if(errors === _errs3){
if(Array.isArray(data1)){
var valid1 = true;
const len0 = data1.length;
for(let i0=0; i0<len0; i0++){
const _errs5 = errors;
if(!(validate48(data1[i0], {instancePath:instancePath+"/messages/" + i0,parentData:data1,parentDataProperty:i0,rootData,dynamicAnchors}))){
vErrors = vErrors === null ? validate48.errors : vErrors.concat(validate48.errors);
errors = vErrors.length;
}
var valid1 = _errs5 === errors;
if(!valid1){
break;
}
}
}
else {
validate47.errors = [{instancePath:instancePath+"/messages",schemaPath:"#/properties/messages/type",keyword:"type",params:{type: "array"},message:"must be array"}];
return false;
}
}
var valid0 = _errs3 === errors;
}
else {
var valid0 = true;
}
}
}
}
else {
validate47.errors = [{instancePath,schemaPath:"#/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
validate47.errors = vErrors;
return errors === 0;
}
validate47.evaluated = {"props":{"before":true,"messages":true},"dynamicProps":false,"dynamicItems":false};


function validate33(data, {instancePath="", parentData, parentDataProperty, rootData=data, dynamicAnchors={}}={}){
let vErrors = null;
let errors = 0;
const evaluated0 = validate33.evaluated;
if(evaluated0.dynamicProps){
evaluated0.props = undefined;
}
if(evaluated0.dynamicItems){
evaluated0.items = undefined;
}
const _errs0 = errors;
let valid0 = false;
let passing0 = null;
const _errs1 = errors;
if(errors === _errs1){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing0;
if(((data.kind === undefined) && (missing0 = "kind")) || ((data.response === undefined) && (missing0 = "response"))){
const err0 = {instancePath,schemaPath:"#/oneOf/0/required",keyword:"required",params:{missingProperty: missing0},message:"must have required property '"+missing0+"'"};
if(vErrors === null){
vErrors = [err0];
}
else {
vErrors.push(err0);
}
errors++;
}
else {
if(data.kind !== undefined){
let data0 = data.kind;
const _errs3 = errors;
if(typeof data0 !== "string"){
const err1 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/0/properties/kind/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err1];
}
else {
vErrors.push(err1);
}
errors++;
}
if("networks" !== data0){
const err2 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/0/properties/kind/const",keyword:"const",params:{allowedValue: "networks"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err2];
}
else {
vErrors.push(err2);
}
errors++;
}
var valid1 = _errs3 === errors;
}
else {
var valid1 = true;
}
if(valid1){
if(data.response !== undefined){
const _errs5 = errors;
if(!(root0.validate(data.response, {instancePath:instancePath+"/response",parentData:data,parentDataProperty:"response",rootData,dynamicAnchors}))){
vErrors = vErrors === null ? root0.validate.errors : vErrors.concat(root0.validate.errors);
errors = vErrors.length;
}
var valid1 = _errs5 === errors;
}
else {
var valid1 = true;
}
}
}
}
else {
const err3 = {instancePath,schemaPath:"#/oneOf/0/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err3];
}
else {
vErrors.push(err3);
}
errors++;
}
}
var _valid0 = _errs1 === errors;
if(_valid0){
valid0 = true;
passing0 = 0;
var props1 = {};
props1.kind = true;
props1.response = true;
}
const _errs6 = errors;
if(errors === _errs6){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing1;
if(((data.kind === undefined) && (missing1 = "kind")) || ((data.snapshot === undefined) && (missing1 = "snapshot"))){
const err4 = {instancePath,schemaPath:"#/oneOf/1/required",keyword:"required",params:{missingProperty: missing1},message:"must have required property '"+missing1+"'"};
if(vErrors === null){
vErrors = [err4];
}
else {
vErrors.push(err4);
}
errors++;
}
else {
if(data.kind !== undefined){
let data2 = data.kind;
const _errs8 = errors;
if(typeof data2 !== "string"){
const err5 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/1/properties/kind/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err5];
}
else {
vErrors.push(err5);
}
errors++;
}
if("files" !== data2){
const err6 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/1/properties/kind/const",keyword:"const",params:{allowedValue: "files"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err6];
}
else {
vErrors.push(err6);
}
errors++;
}
var valid2 = _errs8 === errors;
}
else {
var valid2 = true;
}
if(valid2){
if(data.snapshot !== undefined){
const _errs10 = errors;
if(!(validate34(data.snapshot, {instancePath:instancePath+"/snapshot",parentData:data,parentDataProperty:"snapshot",rootData,dynamicAnchors}))){
vErrors = vErrors === null ? validate34.errors : vErrors.concat(validate34.errors);
errors = vErrors.length;
}
var valid2 = _errs10 === errors;
}
else {
var valid2 = true;
}
}
}
}
else {
const err7 = {instancePath,schemaPath:"#/oneOf/1/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err7];
}
else {
vErrors.push(err7);
}
errors++;
}
}
var _valid0 = _errs6 === errors;
if(_valid0 && valid0){
valid0 = false;
passing0 = [passing0, 1];
}
else {
if(_valid0){
valid0 = true;
passing0 = 1;
if(props1 !== true){
props1 = props1 || {};
props1.kind = true;
props1.snapshot = true;
}
}
const _errs11 = errors;
if(errors === _errs11){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing2;
if(((data.kind === undefined) && (missing2 = "kind")) || ((data.status === undefined) && (missing2 = "status"))){
const err8 = {instancePath,schemaPath:"#/oneOf/2/required",keyword:"required",params:{missingProperty: missing2},message:"must have required property '"+missing2+"'"};
if(vErrors === null){
vErrors = [err8];
}
else {
vErrors.push(err8);
}
errors++;
}
else {
if(data.kind !== undefined){
let data4 = data.kind;
const _errs13 = errors;
if(typeof data4 !== "string"){
const err9 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/2/properties/kind/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err9];
}
else {
vErrors.push(err9);
}
errors++;
}
if("network_status" !== data4){
const err10 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/2/properties/kind/const",keyword:"const",params:{allowedValue: "network_status"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err10];
}
else {
vErrors.push(err10);
}
errors++;
}
var valid3 = _errs13 === errors;
}
else {
var valid3 = true;
}
if(valid3){
if(data.status !== undefined){
const _errs15 = errors;
if(!(validate27(data.status, {instancePath:instancePath+"/status",parentData:data,parentDataProperty:"status",rootData,dynamicAnchors}))){
vErrors = vErrors === null ? validate27.errors : vErrors.concat(validate27.errors);
errors = vErrors.length;
}
var valid3 = _errs15 === errors;
}
else {
var valid3 = true;
}
}
}
}
else {
const err11 = {instancePath,schemaPath:"#/oneOf/2/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err11];
}
else {
vErrors.push(err11);
}
errors++;
}
}
var _valid0 = _errs11 === errors;
if(_valid0 && valid0){
valid0 = false;
passing0 = [passing0, 2];
}
else {
if(_valid0){
valid0 = true;
passing0 = 2;
if(props1 !== true){
props1 = props1 || {};
props1.kind = true;
props1.status = true;
}
}
const _errs16 = errors;
if(errors === _errs16){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing3;
if(((data.kind === undefined) && (missing3 = "kind")) || ((data.instance === undefined) && (missing3 = "instance"))){
const err12 = {instancePath,schemaPath:"#/oneOf/3/required",keyword:"required",params:{missingProperty: missing3},message:"must have required property '"+missing3+"'"};
if(vErrors === null){
vErrors = [err12];
}
else {
vErrors.push(err12);
}
errors++;
}
else {
if(data.instance !== undefined){
let data6 = data.instance;
const _errs18 = errors;
const _errs19 = errors;
if(errors === _errs19){
if(data6 && typeof data6 == "object" && !Array.isArray(data6)){
let missing4;
if((((((((((data6.id === undefined) && (missing4 = "id")) || ((data6.label === undefined) && (missing4 = "label"))) || ((data6.bootId === undefined) && (missing4 = "bootId"))) || ((data6.locked === undefined) && (missing4 = "locked"))) || ((data6.protocolLocked === undefined) && (missing4 = "protocolLocked"))) || ((data6.profileExists === undefined) && (missing4 = "profileExists"))) || ((data6.archiveExists === undefined) && (missing4 = "archiveExists"))) || ((data6.safetyNumber === undefined) && (missing4 = "safetyNumber"))) || ((data6.capabilities === undefined) && (missing4 = "capabilities"))){
const err13 = {instancePath:instancePath+"/instance",schemaPath:"#/$defs/InstanceInfo/required",keyword:"required",params:{missingProperty: missing4},message:"must have required property '"+missing4+"'"};
if(vErrors === null){
vErrors = [err13];
}
else {
vErrors.push(err13);
}
errors++;
}
else {
if(data6.archiveExists !== undefined){
const _errs21 = errors;
if(typeof data6.archiveExists !== "boolean"){
const err14 = {instancePath:instancePath+"/instance/archiveExists",schemaPath:"#/$defs/InstanceInfo/properties/archiveExists/type",keyword:"type",params:{type: "boolean"},message:"must be boolean"};
if(vErrors === null){
vErrors = [err14];
}
else {
vErrors.push(err14);
}
errors++;
}
var valid6 = _errs21 === errors;
}
else {
var valid6 = true;
}
if(valid6){
if(data6.bootId !== undefined){
const _errs23 = errors;
if(typeof data6.bootId !== "string"){
const err15 = {instancePath:instancePath+"/instance/bootId",schemaPath:"#/$defs/InstanceInfo/properties/bootId/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err15];
}
else {
vErrors.push(err15);
}
errors++;
}
var valid6 = _errs23 === errors;
}
else {
var valid6 = true;
}
if(valid6){
if(data6.capabilities !== undefined){
let data9 = data6.capabilities;
const _errs25 = errors;
if(errors === _errs25){
if(Array.isArray(data9)){
var valid7 = true;
const len0 = data9.length;
for(let i0=0; i0<len0; i0++){
const _errs27 = errors;
if(typeof data9[i0] !== "string"){
const err16 = {instancePath:instancePath+"/instance/capabilities/" + i0,schemaPath:"#/$defs/InstanceInfo/properties/capabilities/items/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err16];
}
else {
vErrors.push(err16);
}
errors++;
}
var valid7 = _errs27 === errors;
if(!valid7){
break;
}
}
}
else {
const err17 = {instancePath:instancePath+"/instance/capabilities",schemaPath:"#/$defs/InstanceInfo/properties/capabilities/type",keyword:"type",params:{type: "array"},message:"must be array"};
if(vErrors === null){
vErrors = [err17];
}
else {
vErrors.push(err17);
}
errors++;
}
}
var valid6 = _errs25 === errors;
}
else {
var valid6 = true;
}
if(valid6){
if(data6.id !== undefined){
const _errs29 = errors;
if(typeof data6.id !== "string"){
const err18 = {instancePath:instancePath+"/instance/id",schemaPath:"#/$defs/InstanceInfo/properties/id/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err18];
}
else {
vErrors.push(err18);
}
errors++;
}
var valid6 = _errs29 === errors;
}
else {
var valid6 = true;
}
if(valid6){
if(data6.label !== undefined){
const _errs31 = errors;
if(typeof data6.label !== "string"){
const err19 = {instancePath:instancePath+"/instance/label",schemaPath:"#/$defs/InstanceInfo/properties/label/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err19];
}
else {
vErrors.push(err19);
}
errors++;
}
var valid6 = _errs31 === errors;
}
else {
var valid6 = true;
}
if(valid6){
if(data6.locked !== undefined){
const _errs33 = errors;
if(typeof data6.locked !== "boolean"){
const err20 = {instancePath:instancePath+"/instance/locked",schemaPath:"#/$defs/InstanceInfo/properties/locked/type",keyword:"type",params:{type: "boolean"},message:"must be boolean"};
if(vErrors === null){
vErrors = [err20];
}
else {
vErrors.push(err20);
}
errors++;
}
var valid6 = _errs33 === errors;
}
else {
var valid6 = true;
}
if(valid6){
if(data6.profileExists !== undefined){
const _errs35 = errors;
if(typeof data6.profileExists !== "boolean"){
const err21 = {instancePath:instancePath+"/instance/profileExists",schemaPath:"#/$defs/InstanceInfo/properties/profileExists/type",keyword:"type",params:{type: "boolean"},message:"must be boolean"};
if(vErrors === null){
vErrors = [err21];
}
else {
vErrors.push(err21);
}
errors++;
}
var valid6 = _errs35 === errors;
}
else {
var valid6 = true;
}
if(valid6){
if(data6.protocolLocked !== undefined){
const _errs37 = errors;
if(typeof data6.protocolLocked !== "boolean"){
const err22 = {instancePath:instancePath+"/instance/protocolLocked",schemaPath:"#/$defs/InstanceInfo/properties/protocolLocked/type",keyword:"type",params:{type: "boolean"},message:"must be boolean"};
if(vErrors === null){
vErrors = [err22];
}
else {
vErrors.push(err22);
}
errors++;
}
var valid6 = _errs37 === errors;
}
else {
var valid6 = true;
}
if(valid6){
if(data6.safetyNumber !== undefined){
const _errs39 = errors;
if(typeof data6.safetyNumber !== "string"){
const err23 = {instancePath:instancePath+"/instance/safetyNumber",schemaPath:"#/$defs/InstanceInfo/properties/safetyNumber/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err23];
}
else {
vErrors.push(err23);
}
errors++;
}
var valid6 = _errs39 === errors;
}
else {
var valid6 = true;
}
}
}
}
}
}
}
}
}
}
}
else {
const err24 = {instancePath:instancePath+"/instance",schemaPath:"#/$defs/InstanceInfo/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err24];
}
else {
vErrors.push(err24);
}
errors++;
}
}
var valid4 = _errs18 === errors;
}
else {
var valid4 = true;
}
if(valid4){
if(data.kind !== undefined){
let data17 = data.kind;
const _errs41 = errors;
if(typeof data17 !== "string"){
const err25 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/3/properties/kind/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err25];
}
else {
vErrors.push(err25);
}
errors++;
}
if("instance" !== data17){
const err26 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/3/properties/kind/const",keyword:"const",params:{allowedValue: "instance"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err26];
}
else {
vErrors.push(err26);
}
errors++;
}
var valid4 = _errs41 === errors;
}
else {
var valid4 = true;
}
}
}
}
else {
const err27 = {instancePath,schemaPath:"#/oneOf/3/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err27];
}
else {
vErrors.push(err27);
}
errors++;
}
}
var _valid0 = _errs16 === errors;
if(_valid0 && valid0){
valid0 = false;
passing0 = [passing0, 3];
}
else {
if(_valid0){
valid0 = true;
passing0 = 3;
if(props1 !== true){
props1 = props1 || {};
props1.instance = true;
props1.kind = true;
}
}
const _errs43 = errors;
if(errors === _errs43){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing5;
if(((data.kind === undefined) && (missing5 = "kind")) || ((data.snapshot === undefined) && (missing5 = "snapshot"))){
const err28 = {instancePath,schemaPath:"#/oneOf/4/required",keyword:"required",params:{missingProperty: missing5},message:"must have required property '"+missing5+"'"};
if(vErrors === null){
vErrors = [err28];
}
else {
vErrors.push(err28);
}
errors++;
}
else {
if(data.kind !== undefined){
let data18 = data.kind;
const _errs45 = errors;
if(typeof data18 !== "string"){
const err29 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/4/properties/kind/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err29];
}
else {
vErrors.push(err29);
}
errors++;
}
if("snapshot" !== data18){
const err30 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/4/properties/kind/const",keyword:"const",params:{allowedValue: "snapshot"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err30];
}
else {
vErrors.push(err30);
}
errors++;
}
var valid8 = _errs45 === errors;
}
else {
var valid8 = true;
}
if(valid8){
if(data.snapshot !== undefined){
const _errs47 = errors;
if(!(validate39(data.snapshot, {instancePath:instancePath+"/snapshot",parentData:data,parentDataProperty:"snapshot",rootData,dynamicAnchors}))){
vErrors = vErrors === null ? validate39.errors : vErrors.concat(validate39.errors);
errors = vErrors.length;
}
var valid8 = _errs47 === errors;
}
else {
var valid8 = true;
}
}
}
}
else {
const err31 = {instancePath,schemaPath:"#/oneOf/4/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err31];
}
else {
vErrors.push(err31);
}
errors++;
}
}
var _valid0 = _errs43 === errors;
if(_valid0 && valid0){
valid0 = false;
passing0 = [passing0, 4];
}
else {
if(_valid0){
valid0 = true;
passing0 = 4;
if(props1 !== true){
props1 = props1 || {};
props1.kind = true;
props1.snapshot = true;
}
}
const _errs48 = errors;
if(errors === _errs48){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing6;
if(((data.kind === undefined) && (missing6 = "kind")) || ((data.page === undefined) && (missing6 = "page"))){
const err32 = {instancePath,schemaPath:"#/oneOf/5/required",keyword:"required",params:{missingProperty: missing6},message:"must have required property '"+missing6+"'"};
if(vErrors === null){
vErrors = [err32];
}
else {
vErrors.push(err32);
}
errors++;
}
else {
if(data.kind !== undefined){
let data20 = data.kind;
const _errs50 = errors;
if(typeof data20 !== "string"){
const err33 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/5/properties/kind/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err33];
}
else {
vErrors.push(err33);
}
errors++;
}
if("history" !== data20){
const err34 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/5/properties/kind/const",keyword:"const",params:{allowedValue: "history"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err34];
}
else {
vErrors.push(err34);
}
errors++;
}
var valid9 = _errs50 === errors;
}
else {
var valid9 = true;
}
if(valid9){
if(data.page !== undefined){
const _errs52 = errors;
if(!(validate47(data.page, {instancePath:instancePath+"/page",parentData:data,parentDataProperty:"page",rootData,dynamicAnchors}))){
vErrors = vErrors === null ? validate47.errors : vErrors.concat(validate47.errors);
errors = vErrors.length;
}
var valid9 = _errs52 === errors;
}
else {
var valid9 = true;
}
}
}
}
else {
const err35 = {instancePath,schemaPath:"#/oneOf/5/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err35];
}
else {
vErrors.push(err35);
}
errors++;
}
}
var _valid0 = _errs48 === errors;
if(_valid0 && valid0){
valid0 = false;
passing0 = [passing0, 5];
}
else {
if(_valid0){
valid0 = true;
passing0 = 5;
if(props1 !== true){
props1 = props1 || {};
props1.kind = true;
props1.page = true;
}
}
const _errs53 = errors;
if(errors === _errs53){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing7;
if(((data.kind === undefined) && (missing7 = "kind")) || ((data.items === undefined) && (missing7 = "items"))){
const err36 = {instancePath,schemaPath:"#/oneOf/6/required",keyword:"required",params:{missingProperty: missing7},message:"must have required property '"+missing7+"'"};
if(vErrors === null){
vErrors = [err36];
}
else {
vErrors.push(err36);
}
errors++;
}
else {
if(data.items !== undefined){
let data22 = data.items;
const _errs55 = errors;
if(errors === _errs55){
if(Array.isArray(data22)){
var valid11 = true;
const len1 = data22.length;
for(let i1=0; i1<len1; i1++){
let data23 = data22[i1];
const _errs57 = errors;
const _errs58 = errors;
if(errors === _errs58){
if(data23 && typeof data23 == "object" && !Array.isArray(data23)){
let missing8;
if(((data23.text === undefined) && (missing8 = "text")) || ((data23.description === undefined) && (missing8 = "description"))){
const err37 = {instancePath:instancePath+"/items/" + i1,schemaPath:"#/$defs/Completion/required",keyword:"required",params:{missingProperty: missing8},message:"must have required property '"+missing8+"'"};
if(vErrors === null){
vErrors = [err37];
}
else {
vErrors.push(err37);
}
errors++;
}
else {
if(data23.description !== undefined){
const _errs60 = errors;
if(typeof data23.description !== "string"){
const err38 = {instancePath:instancePath+"/items/" + i1+"/description",schemaPath:"#/$defs/Completion/properties/description/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err38];
}
else {
vErrors.push(err38);
}
errors++;
}
var valid13 = _errs60 === errors;
}
else {
var valid13 = true;
}
if(valid13){
if(data23.text !== undefined){
const _errs62 = errors;
if(typeof data23.text !== "string"){
const err39 = {instancePath:instancePath+"/items/" + i1+"/text",schemaPath:"#/$defs/Completion/properties/text/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err39];
}
else {
vErrors.push(err39);
}
errors++;
}
var valid13 = _errs62 === errors;
}
else {
var valid13 = true;
}
}
}
}
else {
const err40 = {instancePath:instancePath+"/items/" + i1,schemaPath:"#/$defs/Completion/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err40];
}
else {
vErrors.push(err40);
}
errors++;
}
}
var valid11 = _errs57 === errors;
if(!valid11){
break;
}
}
}
else {
const err41 = {instancePath:instancePath+"/items",schemaPath:"#/oneOf/6/properties/items/type",keyword:"type",params:{type: "array"},message:"must be array"};
if(vErrors === null){
vErrors = [err41];
}
else {
vErrors.push(err41);
}
errors++;
}
}
var valid10 = _errs55 === errors;
}
else {
var valid10 = true;
}
if(valid10){
if(data.kind !== undefined){
let data26 = data.kind;
const _errs64 = errors;
if(typeof data26 !== "string"){
const err42 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/6/properties/kind/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err42];
}
else {
vErrors.push(err42);
}
errors++;
}
if("completed" !== data26){
const err43 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/6/properties/kind/const",keyword:"const",params:{allowedValue: "completed"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err43];
}
else {
vErrors.push(err43);
}
errors++;
}
var valid10 = _errs64 === errors;
}
else {
var valid10 = true;
}
}
}
}
else {
const err44 = {instancePath,schemaPath:"#/oneOf/6/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err44];
}
else {
vErrors.push(err44);
}
errors++;
}
}
var _valid0 = _errs53 === errors;
if(_valid0 && valid0){
valid0 = false;
passing0 = [passing0, 6];
}
else {
if(_valid0){
valid0 = true;
passing0 = 6;
if(props1 !== true){
props1 = props1 || {};
props1.items = true;
props1.kind = true;
}
}
const _errs66 = errors;
if(errors === _errs66){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing9;
if(((data.kind === undefined) && (missing9 = "kind")) || ((data.commands === undefined) && (missing9 = "commands"))){
const err45 = {instancePath,schemaPath:"#/oneOf/7/required",keyword:"required",params:{missingProperty: missing9},message:"must have required property '"+missing9+"'"};
if(vErrors === null){
vErrors = [err45];
}
else {
vErrors.push(err45);
}
errors++;
}
else {
if(data.commands !== undefined){
let data27 = data.commands;
const _errs68 = errors;
if(errors === _errs68){
if(Array.isArray(data27)){
var valid15 = true;
const len2 = data27.length;
for(let i2=0; i2<len2; i2++){
let data28 = data27[i2];
const _errs70 = errors;
const _errs71 = errors;
if(errors === _errs71){
if(data28 && typeof data28 == "object" && !Array.isArray(data28)){
let missing10;
if((((((data28.name === undefined) && (missing10 = "name")) || ((data28.usage === undefined) && (missing10 = "usage"))) || ((data28.description === undefined) && (missing10 = "description"))) || ((data28.scope === undefined) && (missing10 = "scope"))) || ((data28.available === undefined) && (missing10 = "available"))){
const err46 = {instancePath:instancePath+"/commands/" + i2,schemaPath:"#/$defs/CommandSpec/required",keyword:"required",params:{missingProperty: missing10},message:"must have required property '"+missing10+"'"};
if(vErrors === null){
vErrors = [err46];
}
else {
vErrors.push(err46);
}
errors++;
}
else {
if(data28.available !== undefined){
const _errs73 = errors;
if(typeof data28.available !== "boolean"){
const err47 = {instancePath:instancePath+"/commands/" + i2+"/available",schemaPath:"#/$defs/CommandSpec/properties/available/type",keyword:"type",params:{type: "boolean"},message:"must be boolean"};
if(vErrors === null){
vErrors = [err47];
}
else {
vErrors.push(err47);
}
errors++;
}
var valid17 = _errs73 === errors;
}
else {
var valid17 = true;
}
if(valid17){
if(data28.capability !== undefined){
let data30 = data28.capability;
const _errs75 = errors;
if((typeof data30 !== "string") && (data30 !== null)){
const err48 = {instancePath:instancePath+"/commands/" + i2+"/capability",schemaPath:"#/$defs/CommandSpec/properties/capability/type",keyword:"type",params:{type: schema48.properties.capability.type},message:"must be string,null"};
if(vErrors === null){
vErrors = [err48];
}
else {
vErrors.push(err48);
}
errors++;
}
var valid17 = _errs75 === errors;
}
else {
var valid17 = true;
}
if(valid17){
if(data28.description !== undefined){
const _errs77 = errors;
if(typeof data28.description !== "string"){
const err49 = {instancePath:instancePath+"/commands/" + i2+"/description",schemaPath:"#/$defs/CommandSpec/properties/description/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err49];
}
else {
vErrors.push(err49);
}
errors++;
}
var valid17 = _errs77 === errors;
}
else {
var valid17 = true;
}
if(valid17){
if(data28.name !== undefined){
const _errs79 = errors;
if(typeof data28.name !== "string"){
const err50 = {instancePath:instancePath+"/commands/" + i2+"/name",schemaPath:"#/$defs/CommandSpec/properties/name/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err50];
}
else {
vErrors.push(err50);
}
errors++;
}
var valid17 = _errs79 === errors;
}
else {
var valid17 = true;
}
if(valid17){
if(data28.scope !== undefined){
const _errs81 = errors;
if(typeof data28.scope !== "string"){
const err51 = {instancePath:instancePath+"/commands/" + i2+"/scope",schemaPath:"#/$defs/CommandSpec/properties/scope/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err51];
}
else {
vErrors.push(err51);
}
errors++;
}
var valid17 = _errs81 === errors;
}
else {
var valid17 = true;
}
if(valid17){
if(data28.usage !== undefined){
const _errs83 = errors;
if(typeof data28.usage !== "string"){
const err52 = {instancePath:instancePath+"/commands/" + i2+"/usage",schemaPath:"#/$defs/CommandSpec/properties/usage/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err52];
}
else {
vErrors.push(err52);
}
errors++;
}
var valid17 = _errs83 === errors;
}
else {
var valid17 = true;
}
}
}
}
}
}
}
}
else {
const err53 = {instancePath:instancePath+"/commands/" + i2,schemaPath:"#/$defs/CommandSpec/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err53];
}
else {
vErrors.push(err53);
}
errors++;
}
}
var valid15 = _errs70 === errors;
if(!valid15){
break;
}
}
}
else {
const err54 = {instancePath:instancePath+"/commands",schemaPath:"#/oneOf/7/properties/commands/type",keyword:"type",params:{type: "array"},message:"must be array"};
if(vErrors === null){
vErrors = [err54];
}
else {
vErrors.push(err54);
}
errors++;
}
}
var valid14 = _errs68 === errors;
}
else {
var valid14 = true;
}
if(valid14){
if(data.kind !== undefined){
let data35 = data.kind;
const _errs85 = errors;
if(typeof data35 !== "string"){
const err55 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/7/properties/kind/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err55];
}
else {
vErrors.push(err55);
}
errors++;
}
if("catalogue" !== data35){
const err56 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/7/properties/kind/const",keyword:"const",params:{allowedValue: "catalogue"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err56];
}
else {
vErrors.push(err56);
}
errors++;
}
var valid14 = _errs85 === errors;
}
else {
var valid14 = true;
}
}
}
}
else {
const err57 = {instancePath,schemaPath:"#/oneOf/7/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err57];
}
else {
vErrors.push(err57);
}
errors++;
}
}
var _valid0 = _errs66 === errors;
if(_valid0 && valid0){
valid0 = false;
passing0 = [passing0, 7];
}
else {
if(_valid0){
valid0 = true;
passing0 = 7;
if(props1 !== true){
props1 = props1 || {};
props1.commands = true;
props1.kind = true;
}
}
const _errs87 = errors;
if(errors === _errs87){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing11;
if((((data.kind === undefined) && (missing11 = "kind")) || ((data.conversations === undefined) && (missing11 = "conversations"))) || ((data.revision === undefined) && (missing11 = "revision"))){
const err58 = {instancePath,schemaPath:"#/oneOf/8/required",keyword:"required",params:{missingProperty: missing11},message:"must have required property '"+missing11+"'"};
if(vErrors === null){
vErrors = [err58];
}
else {
vErrors.push(err58);
}
errors++;
}
else {
if(data.conversations !== undefined){
let data36 = data.conversations;
const _errs89 = errors;
if(errors === _errs89){
if(Array.isArray(data36)){
var valid19 = true;
const len3 = data36.length;
for(let i3=0; i3<len3; i3++){
const _errs91 = errors;
if(!(validate40(data36[i3], {instancePath:instancePath+"/conversations/" + i3,parentData:data36,parentDataProperty:i3,rootData,dynamicAnchors}))){
vErrors = vErrors === null ? validate40.errors : vErrors.concat(validate40.errors);
errors = vErrors.length;
}
var valid19 = _errs91 === errors;
if(!valid19){
break;
}
}
}
else {
const err59 = {instancePath:instancePath+"/conversations",schemaPath:"#/oneOf/8/properties/conversations/type",keyword:"type",params:{type: "array"},message:"must be array"};
if(vErrors === null){
vErrors = [err59];
}
else {
vErrors.push(err59);
}
errors++;
}
}
var valid18 = _errs89 === errors;
}
else {
var valid18 = true;
}
if(valid18){
if(data.kind !== undefined){
let data38 = data.kind;
const _errs92 = errors;
if(typeof data38 !== "string"){
const err60 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/8/properties/kind/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err60];
}
else {
vErrors.push(err60);
}
errors++;
}
if("projection" !== data38){
const err61 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/8/properties/kind/const",keyword:"const",params:{allowedValue: "projection"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err61];
}
else {
vErrors.push(err61);
}
errors++;
}
var valid18 = _errs92 === errors;
}
else {
var valid18 = true;
}
if(valid18){
if(data.revision !== undefined){
const _errs94 = errors;
if(typeof data.revision !== "string"){
const err62 = {instancePath:instancePath+"/revision",schemaPath:"#/oneOf/8/properties/revision/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err62];
}
else {
vErrors.push(err62);
}
errors++;
}
var valid18 = _errs94 === errors;
}
else {
var valid18 = true;
}
}
}
}
}
else {
const err63 = {instancePath,schemaPath:"#/oneOf/8/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err63];
}
else {
vErrors.push(err63);
}
errors++;
}
}
var _valid0 = _errs87 === errors;
if(_valid0 && valid0){
valid0 = false;
passing0 = [passing0, 8];
}
else {
if(_valid0){
valid0 = true;
passing0 = 8;
if(props1 !== true){
props1 = props1 || {};
props1.conversations = true;
props1.kind = true;
props1.revision = true;
}
}
const _errs96 = errors;
if(errors === _errs96){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing12;
if(((data.kind === undefined) && (missing12 = "kind")) || ((data.output === undefined) && (missing12 = "output"))){
const err64 = {instancePath,schemaPath:"#/oneOf/9/required",keyword:"required",params:{missingProperty: missing12},message:"must have required property '"+missing12+"'"};
if(vErrors === null){
vErrors = [err64];
}
else {
vErrors.push(err64);
}
errors++;
}
else {
if(data.conversation !== undefined){
let data40 = data.conversation;
const _errs98 = errors;
if((typeof data40 !== "string") && (data40 !== null)){
const err65 = {instancePath:instancePath+"/conversation",schemaPath:"#/oneOf/9/properties/conversation/type",keyword:"type",params:{type: schema40.oneOf[9].properties.conversation.type},message:"must be string,null"};
if(vErrors === null){
vErrors = [err65];
}
else {
vErrors.push(err65);
}
errors++;
}
var valid20 = _errs98 === errors;
}
else {
var valid20 = true;
}
if(valid20){
if(data.kind !== undefined){
let data41 = data.kind;
const _errs100 = errors;
if(typeof data41 !== "string"){
const err66 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/9/properties/kind/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err66];
}
else {
vErrors.push(err66);
}
errors++;
}
if("output" !== data41){
const err67 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/9/properties/kind/const",keyword:"const",params:{allowedValue: "output"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err67];
}
else {
vErrors.push(err67);
}
errors++;
}
var valid20 = _errs100 === errors;
}
else {
var valid20 = true;
}
if(valid20){
if(data.output !== undefined){
const _errs102 = errors;
if(!(validate43(data.output, {instancePath:instancePath+"/output",parentData:data,parentDataProperty:"output",rootData,dynamicAnchors}))){
vErrors = vErrors === null ? validate43.errors : vErrors.concat(validate43.errors);
errors = vErrors.length;
}
var valid20 = _errs102 === errors;
}
else {
var valid20 = true;
}
}
}
}
}
else {
const err68 = {instancePath,schemaPath:"#/oneOf/9/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err68];
}
else {
vErrors.push(err68);
}
errors++;
}
}
var _valid0 = _errs96 === errors;
if(_valid0 && valid0){
valid0 = false;
passing0 = [passing0, 9];
}
else {
if(_valid0){
valid0 = true;
passing0 = 9;
if(props1 !== true){
props1 = props1 || {};
props1.conversation = true;
props1.kind = true;
props1.output = true;
}
}
const _errs103 = errors;
if(errors === _errs103){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing13;
if((data.kind === undefined) && (missing13 = "kind")){
const err69 = {instancePath,schemaPath:"#/oneOf/10/required",keyword:"required",params:{missingProperty: missing13},message:"must have required property '"+missing13+"'"};
if(vErrors === null){
vErrors = [err69];
}
else {
vErrors.push(err69);
}
errors++;
}
else {
if(data.conversation !== undefined){
let data43 = data.conversation;
const _errs105 = errors;
if((typeof data43 !== "string") && (data43 !== null)){
const err70 = {instancePath:instancePath+"/conversation",schemaPath:"#/oneOf/10/properties/conversation/type",keyword:"type",params:{type: schema40.oneOf[10].properties.conversation.type},message:"must be string,null"};
if(vErrors === null){
vErrors = [err70];
}
else {
vErrors.push(err70);
}
errors++;
}
var valid21 = _errs105 === errors;
}
else {
var valid21 = true;
}
if(valid21){
if(data.kind !== undefined){
let data44 = data.kind;
const _errs107 = errors;
if(typeof data44 !== "string"){
const err71 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/10/properties/kind/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err71];
}
else {
vErrors.push(err71);
}
errors++;
}
if("applied" !== data44){
const err72 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/10/properties/kind/const",keyword:"const",params:{allowedValue: "applied"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err72];
}
else {
vErrors.push(err72);
}
errors++;
}
var valid21 = _errs107 === errors;
}
else {
var valid21 = true;
}
if(valid21){
if(data.notice !== undefined){
let data45 = data.notice;
const _errs109 = errors;
if((typeof data45 !== "string") && (data45 !== null)){
const err73 = {instancePath:instancePath+"/notice",schemaPath:"#/oneOf/10/properties/notice/type",keyword:"type",params:{type: schema40.oneOf[10].properties.notice.type},message:"must be string,null"};
if(vErrors === null){
vErrors = [err73];
}
else {
vErrors.push(err73);
}
errors++;
}
var valid21 = _errs109 === errors;
}
else {
var valid21 = true;
}
}
}
}
}
else {
const err74 = {instancePath,schemaPath:"#/oneOf/10/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err74];
}
else {
vErrors.push(err74);
}
errors++;
}
}
var _valid0 = _errs103 === errors;
if(_valid0 && valid0){
valid0 = false;
passing0 = [passing0, 10];
}
else {
if(_valid0){
valid0 = true;
passing0 = 10;
if(props1 !== true){
props1 = props1 || {};
props1.conversation = true;
props1.kind = true;
props1.notice = true;
}
}
const _errs111 = errors;
if(errors === _errs111){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing14;
if(((data.kind === undefined) && (missing14 = "kind")) || ((data.revision === undefined) && (missing14 = "revision"))){
const err75 = {instancePath,schemaPath:"#/oneOf/11/required",keyword:"required",params:{missingProperty: missing14},message:"must have required property '"+missing14+"'"};
if(vErrors === null){
vErrors = [err75];
}
else {
vErrors.push(err75);
}
errors++;
}
else {
if(data.kind !== undefined){
let data46 = data.kind;
const _errs113 = errors;
if(typeof data46 !== "string"){
const err76 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/11/properties/kind/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err76];
}
else {
vErrors.push(err76);
}
errors++;
}
if("changed" !== data46){
const err77 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/11/properties/kind/const",keyword:"const",params:{allowedValue: "changed"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err77];
}
else {
vErrors.push(err77);
}
errors++;
}
var valid22 = _errs113 === errors;
}
else {
var valid22 = true;
}
if(valid22){
if(data.revision !== undefined){
const _errs115 = errors;
if(typeof data.revision !== "string"){
const err78 = {instancePath:instancePath+"/revision",schemaPath:"#/oneOf/11/properties/revision/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err78];
}
else {
vErrors.push(err78);
}
errors++;
}
var valid22 = _errs115 === errors;
}
else {
var valid22 = true;
}
}
}
}
else {
const err79 = {instancePath,schemaPath:"#/oneOf/11/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err79];
}
else {
vErrors.push(err79);
}
errors++;
}
}
var _valid0 = _errs111 === errors;
if(_valid0 && valid0){
valid0 = false;
passing0 = [passing0, 11];
}
else {
if(_valid0){
valid0 = true;
passing0 = 11;
if(props1 !== true){
props1 = props1 || {};
props1.kind = true;
props1.revision = true;
}
}
const _errs117 = errors;
if(errors === _errs117){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing15;
if((((data.kind === undefined) && (missing15 = "kind")) || ((data.code === undefined) && (missing15 = "code"))) || ((data.message === undefined) && (missing15 = "message"))){
const err80 = {instancePath,schemaPath:"#/oneOf/12/required",keyword:"required",params:{missingProperty: missing15},message:"must have required property '"+missing15+"'"};
if(vErrors === null){
vErrors = [err80];
}
else {
vErrors.push(err80);
}
errors++;
}
else {
if(data.code !== undefined){
const _errs119 = errors;
if(typeof data.code !== "string"){
const err81 = {instancePath:instancePath+"/code",schemaPath:"#/oneOf/12/properties/code/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err81];
}
else {
vErrors.push(err81);
}
errors++;
}
var valid23 = _errs119 === errors;
}
else {
var valid23 = true;
}
if(valid23){
if(data.kind !== undefined){
let data49 = data.kind;
const _errs121 = errors;
if(typeof data49 !== "string"){
const err82 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/12/properties/kind/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err82];
}
else {
vErrors.push(err82);
}
errors++;
}
if("error" !== data49){
const err83 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/12/properties/kind/const",keyword:"const",params:{allowedValue: "error"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err83];
}
else {
vErrors.push(err83);
}
errors++;
}
var valid23 = _errs121 === errors;
}
else {
var valid23 = true;
}
if(valid23){
if(data.message !== undefined){
const _errs123 = errors;
if(typeof data.message !== "string"){
const err84 = {instancePath:instancePath+"/message",schemaPath:"#/oneOf/12/properties/message/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err84];
}
else {
vErrors.push(err84);
}
errors++;
}
var valid23 = _errs123 === errors;
}
else {
var valid23 = true;
}
}
}
}
}
else {
const err85 = {instancePath,schemaPath:"#/oneOf/12/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err85];
}
else {
vErrors.push(err85);
}
errors++;
}
}
var _valid0 = _errs117 === errors;
if(_valid0 && valid0){
valid0 = false;
passing0 = [passing0, 12];
}
else {
if(_valid0){
valid0 = true;
passing0 = 12;
if(props1 !== true){
props1 = props1 || {};
props1.code = true;
props1.kind = true;
props1.message = true;
}
}
}
}
}
}
}
}
}
}
}
}
}
}
if(!valid0){
const err86 = {instancePath,schemaPath:"#/oneOf",keyword:"oneOf",params:{passingSchemas: passing0},message:"must match exactly one schema in oneOf"};
if(vErrors === null){
vErrors = [err86];
}
else {
vErrors.push(err86);
}
errors++;
validate33.errors = vErrors;
return false;
}
else {
errors = _errs0;
if(vErrors !== null){
if(_errs0){
vErrors.length = _errs0;
}
else {
vErrors = null;
}
}
}
validate33.errors = vErrors;
evaluated0.props = props1;
return errors === 0;
}
validate33.evaluated = {"dynamicProps":true,"dynamicItems":false};


function validate25(data, {instancePath="", parentData, parentDataProperty, rootData=data, dynamicAnchors={}}={}){
let vErrors = null;
let errors = 0;
const evaluated0 = validate25.evaluated;
if(evaluated0.dynamicProps){
evaluated0.props = undefined;
}
if(evaluated0.dynamicItems){
evaluated0.items = undefined;
}
const _errs0 = errors;
let valid0 = false;
let passing0 = null;
const _errs1 = errors;
if(errors === _errs1){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing0;
if(((data.kind === undefined) && (missing0 = "kind")) || ((data.networks === undefined) && (missing0 = "networks"))){
const err0 = {instancePath,schemaPath:"#/oneOf/0/required",keyword:"required",params:{missingProperty: missing0},message:"must have required property '"+missing0+"'"};
if(vErrors === null){
vErrors = [err0];
}
else {
vErrors.push(err0);
}
errors++;
}
else {
if(data.kind !== undefined){
let data0 = data.kind;
const _errs3 = errors;
if(typeof data0 !== "string"){
const err1 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/0/properties/kind/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err1];
}
else {
vErrors.push(err1);
}
errors++;
}
if("list" !== data0){
const err2 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/0/properties/kind/const",keyword:"const",params:{allowedValue: "list"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err2];
}
else {
vErrors.push(err2);
}
errors++;
}
var valid1 = _errs3 === errors;
}
else {
var valid1 = true;
}
if(valid1){
if(data.networks !== undefined){
let data1 = data.networks;
const _errs5 = errors;
if(errors === _errs5){
if(Array.isArray(data1)){
var valid2 = true;
const len0 = data1.length;
for(let i0=0; i0<len0; i0++){
const _errs7 = errors;
if(!(validate26(data1[i0], {instancePath:instancePath+"/networks/" + i0,parentData:data1,parentDataProperty:i0,rootData,dynamicAnchors}))){
vErrors = vErrors === null ? validate26.errors : vErrors.concat(validate26.errors);
errors = vErrors.length;
}
var valid2 = _errs7 === errors;
if(!valid2){
break;
}
}
}
else {
const err3 = {instancePath:instancePath+"/networks",schemaPath:"#/oneOf/0/properties/networks/type",keyword:"type",params:{type: "array"},message:"must be array"};
if(vErrors === null){
vErrors = [err3];
}
else {
vErrors.push(err3);
}
errors++;
}
}
var valid1 = _errs5 === errors;
}
else {
var valid1 = true;
}
}
}
}
else {
const err4 = {instancePath,schemaPath:"#/oneOf/0/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err4];
}
else {
vErrors.push(err4);
}
errors++;
}
}
var _valid0 = _errs1 === errors;
if(_valid0){
valid0 = true;
passing0 = 0;
var props0 = {};
props0.kind = true;
props0.networks = true;
}
const _errs8 = errors;
if(errors === _errs8){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing1;
if(((data.kind === undefined) && (missing1 = "kind")) || ((data.preview === undefined) && (missing1 = "preview"))){
const err5 = {instancePath,schemaPath:"#/oneOf/1/required",keyword:"required",params:{missingProperty: missing1},message:"must have required property '"+missing1+"'"};
if(vErrors === null){
vErrors = [err5];
}
else {
vErrors.push(err5);
}
errors++;
}
else {
if(data.kind !== undefined){
let data3 = data.kind;
const _errs10 = errors;
if(typeof data3 !== "string"){
const err6 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/1/properties/kind/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err6];
}
else {
vErrors.push(err6);
}
errors++;
}
if("preview" !== data3){
const err7 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/1/properties/kind/const",keyword:"const",params:{allowedValue: "preview"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err7];
}
else {
vErrors.push(err7);
}
errors++;
}
var valid3 = _errs10 === errors;
}
else {
var valid3 = true;
}
if(valid3){
if(data.preview !== undefined){
const _errs12 = errors;
if(!(validate30(data.preview, {instancePath:instancePath+"/preview",parentData:data,parentDataProperty:"preview",rootData,dynamicAnchors}))){
vErrors = vErrors === null ? validate30.errors : vErrors.concat(validate30.errors);
errors = vErrors.length;
}
var valid3 = _errs12 === errors;
}
else {
var valid3 = true;
}
}
}
}
else {
const err8 = {instancePath,schemaPath:"#/oneOf/1/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err8];
}
else {
vErrors.push(err8);
}
errors++;
}
}
var _valid0 = _errs8 === errors;
if(_valid0 && valid0){
valid0 = false;
passing0 = [passing0, 1];
}
else {
if(_valid0){
valid0 = true;
passing0 = 1;
if(props0 !== true){
props0 = props0 || {};
props0.kind = true;
props0.preview = true;
}
}
const _errs13 = errors;
if(errors === _errs13){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing2;
if((((data.kind === undefined) && (missing2 = "kind")) || ((data.network === undefined) && (missing2 = "network"))) || ((data.response === undefined) && (missing2 = "response"))){
const err9 = {instancePath,schemaPath:"#/oneOf/2/required",keyword:"required",params:{missingProperty: missing2},message:"must have required property '"+missing2+"'"};
if(vErrors === null){
vErrors = [err9];
}
else {
vErrors.push(err9);
}
errors++;
}
else {
if(data.kind !== undefined){
let data5 = data.kind;
const _errs15 = errors;
if(typeof data5 !== "string"){
const err10 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/2/properties/kind/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err10];
}
else {
vErrors.push(err10);
}
errors++;
}
if("result" !== data5){
const err11 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/2/properties/kind/const",keyword:"const",params:{allowedValue: "result"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err11];
}
else {
vErrors.push(err11);
}
errors++;
}
var valid4 = _errs15 === errors;
}
else {
var valid4 = true;
}
if(valid4){
if(data.network !== undefined){
const _errs17 = errors;
if(typeof data.network !== "string"){
const err12 = {instancePath:instancePath+"/network",schemaPath:"#/oneOf/2/properties/network/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err12];
}
else {
vErrors.push(err12);
}
errors++;
}
var valid4 = _errs17 === errors;
}
else {
var valid4 = true;
}
if(valid4){
if(data.response !== undefined){
const _errs19 = errors;
if(!(validate33(data.response, {instancePath:instancePath+"/response",parentData:data,parentDataProperty:"response",rootData,dynamicAnchors}))){
vErrors = vErrors === null ? validate33.errors : vErrors.concat(validate33.errors);
errors = vErrors.length;
}
var valid4 = _errs19 === errors;
}
else {
var valid4 = true;
}
}
}
}
}
else {
const err13 = {instancePath,schemaPath:"#/oneOf/2/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err13];
}
else {
vErrors.push(err13);
}
errors++;
}
}
var _valid0 = _errs13 === errors;
if(_valid0 && valid0){
valid0 = false;
passing0 = [passing0, 2];
}
else {
if(_valid0){
valid0 = true;
passing0 = 2;
if(props0 !== true){
props0 = props0 || {};
props0.kind = true;
props0.network = true;
props0.response = true;
}
}
}
}
if(!valid0){
const err14 = {instancePath,schemaPath:"#/oneOf",keyword:"oneOf",params:{passingSchemas: passing0},message:"must match exactly one schema in oneOf"};
if(vErrors === null){
vErrors = [err14];
}
else {
vErrors.push(err14);
}
errors++;
validate25.errors = vErrors;
return false;
}
else {
errors = _errs0;
if(vErrors !== null){
if(_errs0){
vErrors.length = _errs0;
}
else {
vErrors = null;
}
}
}
validate25.errors = vErrors;
evaluated0.props = props0;
return errors === 0;
}
validate25.evaluated = {"dynamicProps":true,"dynamicItems":false};

export const network_operation_error = validate56;
const schema65 = {"$schema":"https://json-schema.org/draft/2020-12/schema","additionalProperties":false,"properties":{"code":{"type":"string"},"message":{"type":"string"}},"required":["code","message"],"title":"ChatError","type":"object"};

function validate56(data, {instancePath="", parentData, parentDataProperty, rootData=data, dynamicAnchors={}}={}){
let vErrors = null;
let errors = 0;
const evaluated0 = validate56.evaluated;
if(evaluated0.dynamicProps){
evaluated0.props = undefined;
}
if(evaluated0.dynamicItems){
evaluated0.items = undefined;
}
if(errors === 0){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing0;
if(((data.code === undefined) && (missing0 = "code")) || ((data.message === undefined) && (missing0 = "message"))){
validate56.errors = [{instancePath,schemaPath:"#/required",keyword:"required",params:{missingProperty: missing0},message:"must have required property '"+missing0+"'"}];
return false;
}
else {
const _errs1 = errors;
for(const key0 in data){
if(!((key0 === "code") || (key0 === "message"))){
validate56.errors = [{instancePath,schemaPath:"#/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key0},message:"must NOT have additional properties"}];
return false;
break;
}
}
if(_errs1 === errors){
if(data.code !== undefined){
const _errs2 = errors;
if(typeof data.code !== "string"){
validate56.errors = [{instancePath:instancePath+"/code",schemaPath:"#/properties/code/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs2 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.message !== undefined){
const _errs4 = errors;
if(typeof data.message !== "string"){
validate56.errors = [{instancePath:instancePath+"/message",schemaPath:"#/properties/message/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs4 === errors;
}
else {
var valid0 = true;
}
}
}
}
}
else {
validate56.errors = [{instancePath,schemaPath:"#/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
validate56.errors = vErrors;
return errors === 0;
}
validate56.evaluated = {"props":true,"dynamicProps":false,"dynamicItems":false};

export const networks_args = validate57;
const schema66 = {"$defs":{"FileRequest":{"oneOf":[{"additionalProperties":false,"properties":{"action":{"const":"list","type":"string"},"conversation":{"type":["string","null"]}},"required":["action"],"type":"object"},{"additionalProperties":false,"properties":{"action":{"const":"prepare","type":"string"},"conversation":{"type":"string"},"id":{"type":"string"},"name":{"type":"string"},"size_bytes":{"type":"string"}},"required":["action","id","conversation","name","size_bytes"],"type":"object"},{"additionalProperties":false,"properties":{"action":{"const":"commit","type":"string"},"id":{"type":"string"}},"required":["action","id"],"type":"object"},{"additionalProperties":false,"properties":{"action":{"const":"accept","type":"string"},"id":{"type":"string"}},"required":["action","id"],"type":"object"},{"additionalProperties":false,"properties":{"action":{"const":"pause","type":"string"},"id":{"type":"string"}},"required":["action","id"],"type":"object"},{"additionalProperties":false,"properties":{"action":{"const":"resume","type":"string"},"id":{"type":"string"}},"required":["action","id"],"type":"object"},{"additionalProperties":false,"properties":{"action":{"const":"cancel","type":"string"},"id":{"type":"string"}},"required":["action","id"],"type":"object"},{"additionalProperties":false,"properties":{"action":{"const":"configure","type":"string"},"quota_bytes":{"type":"string"},"retention_days":{"format":"uint16","maximum":65535,"minimum":0,"type":"integer"}},"required":["action","quota_bytes","retention_days"],"type":"object"}]},"NetworkRequest":{"oneOf":[{"additionalProperties":false,"properties":{"kind":{"const":"list","type":"string"}},"required":["kind"],"type":"object"},{"additionalProperties":false,"properties":{"code":{"type":"string"},"kind":{"const":"inspect","type":"string"}},"required":["kind","code"],"type":"object"},{"additionalProperties":false,"properties":{"accepted_network":{"type":"string"},"code":{"type":"string"},"kind":{"const":"join","type":"string"},"nickname":{"type":"string"},"operation_id":{"type":"string"}},"required":["kind","code","nickname","accepted_network","operation_id"],"type":"object"},{"additionalProperties":false,"properties":{"kind":{"const":"call","type":"string"},"network":{"type":"string"},"request":{"$ref":"#/$defs/Request"}},"required":["kind","network","request"],"type":"object"}]},"Request":{"oneOf":[{"additionalProperties":false,"properties":{"kind":{"const":"networks","type":"string"},"request":{"$ref":"#/$defs/NetworkRequest"}},"required":["kind","request"],"type":"object"},{"additionalProperties":false,"properties":{"kind":{"const":"files","type":"string"},"request":{"$ref":"#/$defs/FileRequest"}},"required":["kind","request"],"type":"object"},{"additionalProperties":false,"properties":{"kind":{"const":"identify","type":"string"}},"required":["kind"],"type":"object"},{"additionalProperties":false,"properties":{"create":{"type":"boolean"},"kind":{"const":"unlock","type":"string"},"passphrase":{"type":"string"}},"required":["kind","passphrase","create"],"type":"object"},{"additionalProperties":false,"properties":{"kind":{"const":"lock","type":"string"}},"required":["kind"],"type":"object"},{"additionalProperties":false,"properties":{"kind":{"const":"disconnect","type":"string"}},"required":["kind"],"type":"object"},{"additionalProperties":false,"properties":{"kind":{"const":"snapshot","type":"string"}},"required":["kind"],"type":"object"},{"additionalProperties":false,"properties":{"kind":{"const":"network_status","type":"string"}},"required":["kind"],"type":"object"},{"additionalProperties":false,"properties":{"code":{"type":"string"},"kind":{"const":"import_network_invitation","type":"string"}},"required":["kind","code"],"type":"object"},{"additionalProperties":false,"properties":{"conversation":{"type":["string","null"]},"kind":{"const":"catalogue","type":"string"}},"required":["kind"],"type":"object"},{"additionalProperties":false,"properties":{"before":{"type":["string","null"]},"conversation":{"type":"string"},"kind":{"const":"history","type":"string"},"limit":{"format":"uint16","maximum":65535,"minimum":0,"type":"integer"}},"required":["kind","conversation","limit"],"type":"object"},{"additionalProperties":false,"properties":{"before":{"type":["string","null"]},"conversation":{"type":"string"},"kind":{"const":"search","type":"string"},"limit":{"format":"uint16","maximum":65535,"minimum":0,"type":"integer"},"text":{"type":"string"}},"required":["kind","conversation","text","limit"],"type":"object"},{"additionalProperties":false,"properties":{"conversation":{"type":["string","null"]},"kind":{"const":"submit","type":"string"},"operation_id":{"type":"string"},"text":{"type":"string"}},"required":["kind","operation_id","text"],"type":"object"},{"additionalProperties":false,"properties":{"conversation":{"type":["string","null"]},"kind":{"const":"complete","type":"string"},"text":{"type":"string"}},"required":["kind","text"],"type":"object"},{"additionalProperties":false,"properties":{"conversation":{"type":"string"},"kind":{"const":"mark_read","type":"string"},"message_id":{"type":"string"}},"required":["kind","conversation","message_id"],"type":"object"},{"additionalProperties":false,"properties":{"after":{"type":"string"},"kind":{"const":"events","type":"string"},"wait_ms":{"format":"uint16","maximum":65535,"minimum":0,"type":"integer"}},"required":["kind","after","wait_ms"],"type":"object"}]}},"$schema":"https://json-schema.org/draft/2020-12/schema","additionalProperties":false,"properties":{"request":{"$ref":"#/$defs/NetworkRequest"}},"required":["request"],"title":"ChatNetworksArgs","type":"object"};
const schema67 = {"oneOf":[{"additionalProperties":false,"properties":{"kind":{"const":"list","type":"string"}},"required":["kind"],"type":"object"},{"additionalProperties":false,"properties":{"code":{"type":"string"},"kind":{"const":"inspect","type":"string"}},"required":["kind","code"],"type":"object"},{"additionalProperties":false,"properties":{"accepted_network":{"type":"string"},"code":{"type":"string"},"kind":{"const":"join","type":"string"},"nickname":{"type":"string"},"operation_id":{"type":"string"}},"required":["kind","code","nickname","accepted_network","operation_id"],"type":"object"},{"additionalProperties":false,"properties":{"kind":{"const":"call","type":"string"},"network":{"type":"string"},"request":{"$ref":"#/$defs/Request"}},"required":["kind","network","request"],"type":"object"}]};
const schema68 = {"oneOf":[{"additionalProperties":false,"properties":{"kind":{"const":"networks","type":"string"},"request":{"$ref":"#/$defs/NetworkRequest"}},"required":["kind","request"],"type":"object"},{"additionalProperties":false,"properties":{"kind":{"const":"files","type":"string"},"request":{"$ref":"#/$defs/FileRequest"}},"required":["kind","request"],"type":"object"},{"additionalProperties":false,"properties":{"kind":{"const":"identify","type":"string"}},"required":["kind"],"type":"object"},{"additionalProperties":false,"properties":{"create":{"type":"boolean"},"kind":{"const":"unlock","type":"string"},"passphrase":{"type":"string"}},"required":["kind","passphrase","create"],"type":"object"},{"additionalProperties":false,"properties":{"kind":{"const":"lock","type":"string"}},"required":["kind"],"type":"object"},{"additionalProperties":false,"properties":{"kind":{"const":"disconnect","type":"string"}},"required":["kind"],"type":"object"},{"additionalProperties":false,"properties":{"kind":{"const":"snapshot","type":"string"}},"required":["kind"],"type":"object"},{"additionalProperties":false,"properties":{"kind":{"const":"network_status","type":"string"}},"required":["kind"],"type":"object"},{"additionalProperties":false,"properties":{"code":{"type":"string"},"kind":{"const":"import_network_invitation","type":"string"}},"required":["kind","code"],"type":"object"},{"additionalProperties":false,"properties":{"conversation":{"type":["string","null"]},"kind":{"const":"catalogue","type":"string"}},"required":["kind"],"type":"object"},{"additionalProperties":false,"properties":{"before":{"type":["string","null"]},"conversation":{"type":"string"},"kind":{"const":"history","type":"string"},"limit":{"format":"uint16","maximum":65535,"minimum":0,"type":"integer"}},"required":["kind","conversation","limit"],"type":"object"},{"additionalProperties":false,"properties":{"before":{"type":["string","null"]},"conversation":{"type":"string"},"kind":{"const":"search","type":"string"},"limit":{"format":"uint16","maximum":65535,"minimum":0,"type":"integer"},"text":{"type":"string"}},"required":["kind","conversation","text","limit"],"type":"object"},{"additionalProperties":false,"properties":{"conversation":{"type":["string","null"]},"kind":{"const":"submit","type":"string"},"operation_id":{"type":"string"},"text":{"type":"string"}},"required":["kind","operation_id","text"],"type":"object"},{"additionalProperties":false,"properties":{"conversation":{"type":["string","null"]},"kind":{"const":"complete","type":"string"},"text":{"type":"string"}},"required":["kind","text"],"type":"object"},{"additionalProperties":false,"properties":{"conversation":{"type":"string"},"kind":{"const":"mark_read","type":"string"},"message_id":{"type":"string"}},"required":["kind","conversation","message_id"],"type":"object"},{"additionalProperties":false,"properties":{"after":{"type":"string"},"kind":{"const":"events","type":"string"},"wait_ms":{"format":"uint16","maximum":65535,"minimum":0,"type":"integer"}},"required":["kind","after","wait_ms"],"type":"object"}]};
const schema69 = {"oneOf":[{"additionalProperties":false,"properties":{"action":{"const":"list","type":"string"},"conversation":{"type":["string","null"]}},"required":["action"],"type":"object"},{"additionalProperties":false,"properties":{"action":{"const":"prepare","type":"string"},"conversation":{"type":"string"},"id":{"type":"string"},"name":{"type":"string"},"size_bytes":{"type":"string"}},"required":["action","id","conversation","name","size_bytes"],"type":"object"},{"additionalProperties":false,"properties":{"action":{"const":"commit","type":"string"},"id":{"type":"string"}},"required":["action","id"],"type":"object"},{"additionalProperties":false,"properties":{"action":{"const":"accept","type":"string"},"id":{"type":"string"}},"required":["action","id"],"type":"object"},{"additionalProperties":false,"properties":{"action":{"const":"pause","type":"string"},"id":{"type":"string"}},"required":["action","id"],"type":"object"},{"additionalProperties":false,"properties":{"action":{"const":"resume","type":"string"},"id":{"type":"string"}},"required":["action","id"],"type":"object"},{"additionalProperties":false,"properties":{"action":{"const":"cancel","type":"string"},"id":{"type":"string"}},"required":["action","id"],"type":"object"},{"additionalProperties":false,"properties":{"action":{"const":"configure","type":"string"},"quota_bytes":{"type":"string"},"retention_days":{"format":"uint16","maximum":65535,"minimum":0,"type":"integer"}},"required":["action","quota_bytes","retention_days"],"type":"object"}]};
const wrapper1 = {validate: validate58};

function validate59(data, {instancePath="", parentData, parentDataProperty, rootData=data, dynamicAnchors={}}={}){
let vErrors = null;
let errors = 0;
const evaluated0 = validate59.evaluated;
if(evaluated0.dynamicProps){
evaluated0.props = undefined;
}
if(evaluated0.dynamicItems){
evaluated0.items = undefined;
}
const _errs0 = errors;
let valid0 = false;
let passing0 = null;
const _errs1 = errors;
if(errors === _errs1){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing0;
if(((data.kind === undefined) && (missing0 = "kind")) || ((data.request === undefined) && (missing0 = "request"))){
const err0 = {instancePath,schemaPath:"#/oneOf/0/required",keyword:"required",params:{missingProperty: missing0},message:"must have required property '"+missing0+"'"};
if(vErrors === null){
vErrors = [err0];
}
else {
vErrors.push(err0);
}
errors++;
}
else {
const _errs3 = errors;
for(const key0 in data){
if(!((key0 === "kind") || (key0 === "request"))){
const err1 = {instancePath,schemaPath:"#/oneOf/0/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key0},message:"must NOT have additional properties"};
if(vErrors === null){
vErrors = [err1];
}
else {
vErrors.push(err1);
}
errors++;
break;
}
}
if(_errs3 === errors){
if(data.kind !== undefined){
let data0 = data.kind;
const _errs4 = errors;
if(typeof data0 !== "string"){
const err2 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/0/properties/kind/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err2];
}
else {
vErrors.push(err2);
}
errors++;
}
if("networks" !== data0){
const err3 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/0/properties/kind/const",keyword:"const",params:{allowedValue: "networks"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err3];
}
else {
vErrors.push(err3);
}
errors++;
}
var valid1 = _errs4 === errors;
}
else {
var valid1 = true;
}
if(valid1){
if(data.request !== undefined){
const _errs6 = errors;
if(!(wrapper1.validate(data.request, {instancePath:instancePath+"/request",parentData:data,parentDataProperty:"request",rootData,dynamicAnchors}))){
vErrors = vErrors === null ? wrapper1.validate.errors : vErrors.concat(wrapper1.validate.errors);
errors = vErrors.length;
}
var valid1 = _errs6 === errors;
}
else {
var valid1 = true;
}
}
}
}
}
else {
const err4 = {instancePath,schemaPath:"#/oneOf/0/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err4];
}
else {
vErrors.push(err4);
}
errors++;
}
}
var _valid0 = _errs1 === errors;
if(_valid0){
valid0 = true;
passing0 = 0;
var props1 = true;
}
const _errs7 = errors;
if(errors === _errs7){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing1;
if(((data.kind === undefined) && (missing1 = "kind")) || ((data.request === undefined) && (missing1 = "request"))){
const err5 = {instancePath,schemaPath:"#/oneOf/1/required",keyword:"required",params:{missingProperty: missing1},message:"must have required property '"+missing1+"'"};
if(vErrors === null){
vErrors = [err5];
}
else {
vErrors.push(err5);
}
errors++;
}
else {
const _errs9 = errors;
for(const key1 in data){
if(!((key1 === "kind") || (key1 === "request"))){
const err6 = {instancePath,schemaPath:"#/oneOf/1/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key1},message:"must NOT have additional properties"};
if(vErrors === null){
vErrors = [err6];
}
else {
vErrors.push(err6);
}
errors++;
break;
}
}
if(_errs9 === errors){
if(data.kind !== undefined){
let data2 = data.kind;
const _errs10 = errors;
if(typeof data2 !== "string"){
const err7 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/1/properties/kind/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err7];
}
else {
vErrors.push(err7);
}
errors++;
}
if("files" !== data2){
const err8 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/1/properties/kind/const",keyword:"const",params:{allowedValue: "files"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err8];
}
else {
vErrors.push(err8);
}
errors++;
}
var valid2 = _errs10 === errors;
}
else {
var valid2 = true;
}
if(valid2){
if(data.request !== undefined){
let data3 = data.request;
const _errs12 = errors;
const _errs14 = errors;
let valid4 = false;
let passing1 = null;
const _errs15 = errors;
if(errors === _errs15){
if(data3 && typeof data3 == "object" && !Array.isArray(data3)){
let missing2;
if((data3.action === undefined) && (missing2 = "action")){
const err9 = {instancePath:instancePath+"/request",schemaPath:"#/$defs/FileRequest/oneOf/0/required",keyword:"required",params:{missingProperty: missing2},message:"must have required property '"+missing2+"'"};
if(vErrors === null){
vErrors = [err9];
}
else {
vErrors.push(err9);
}
errors++;
}
else {
const _errs17 = errors;
for(const key2 in data3){
if(!((key2 === "action") || (key2 === "conversation"))){
const err10 = {instancePath:instancePath+"/request",schemaPath:"#/$defs/FileRequest/oneOf/0/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key2},message:"must NOT have additional properties"};
if(vErrors === null){
vErrors = [err10];
}
else {
vErrors.push(err10);
}
errors++;
break;
}
}
if(_errs17 === errors){
if(data3.action !== undefined){
let data4 = data3.action;
const _errs18 = errors;
if(typeof data4 !== "string"){
const err11 = {instancePath:instancePath+"/request/action",schemaPath:"#/$defs/FileRequest/oneOf/0/properties/action/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err11];
}
else {
vErrors.push(err11);
}
errors++;
}
if("list" !== data4){
const err12 = {instancePath:instancePath+"/request/action",schemaPath:"#/$defs/FileRequest/oneOf/0/properties/action/const",keyword:"const",params:{allowedValue: "list"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err12];
}
else {
vErrors.push(err12);
}
errors++;
}
var valid5 = _errs18 === errors;
}
else {
var valid5 = true;
}
if(valid5){
if(data3.conversation !== undefined){
let data5 = data3.conversation;
const _errs20 = errors;
if((typeof data5 !== "string") && (data5 !== null)){
const err13 = {instancePath:instancePath+"/request/conversation",schemaPath:"#/$defs/FileRequest/oneOf/0/properties/conversation/type",keyword:"type",params:{type: schema69.oneOf[0].properties.conversation.type},message:"must be string,null"};
if(vErrors === null){
vErrors = [err13];
}
else {
vErrors.push(err13);
}
errors++;
}
var valid5 = _errs20 === errors;
}
else {
var valid5 = true;
}
}
}
}
}
else {
const err14 = {instancePath:instancePath+"/request",schemaPath:"#/$defs/FileRequest/oneOf/0/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err14];
}
else {
vErrors.push(err14);
}
errors++;
}
}
var _valid1 = _errs15 === errors;
if(_valid1){
valid4 = true;
passing1 = 0;
var props2 = true;
}
const _errs22 = errors;
if(errors === _errs22){
if(data3 && typeof data3 == "object" && !Array.isArray(data3)){
let missing3;
if((((((data3.action === undefined) && (missing3 = "action")) || ((data3.id === undefined) && (missing3 = "id"))) || ((data3.conversation === undefined) && (missing3 = "conversation"))) || ((data3.name === undefined) && (missing3 = "name"))) || ((data3.size_bytes === undefined) && (missing3 = "size_bytes"))){
const err15 = {instancePath:instancePath+"/request",schemaPath:"#/$defs/FileRequest/oneOf/1/required",keyword:"required",params:{missingProperty: missing3},message:"must have required property '"+missing3+"'"};
if(vErrors === null){
vErrors = [err15];
}
else {
vErrors.push(err15);
}
errors++;
}
else {
const _errs24 = errors;
for(const key3 in data3){
if(!(((((key3 === "action") || (key3 === "conversation")) || (key3 === "id")) || (key3 === "name")) || (key3 === "size_bytes"))){
const err16 = {instancePath:instancePath+"/request",schemaPath:"#/$defs/FileRequest/oneOf/1/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key3},message:"must NOT have additional properties"};
if(vErrors === null){
vErrors = [err16];
}
else {
vErrors.push(err16);
}
errors++;
break;
}
}
if(_errs24 === errors){
if(data3.action !== undefined){
let data6 = data3.action;
const _errs25 = errors;
if(typeof data6 !== "string"){
const err17 = {instancePath:instancePath+"/request/action",schemaPath:"#/$defs/FileRequest/oneOf/1/properties/action/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err17];
}
else {
vErrors.push(err17);
}
errors++;
}
if("prepare" !== data6){
const err18 = {instancePath:instancePath+"/request/action",schemaPath:"#/$defs/FileRequest/oneOf/1/properties/action/const",keyword:"const",params:{allowedValue: "prepare"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err18];
}
else {
vErrors.push(err18);
}
errors++;
}
var valid6 = _errs25 === errors;
}
else {
var valid6 = true;
}
if(valid6){
if(data3.conversation !== undefined){
const _errs27 = errors;
if(typeof data3.conversation !== "string"){
const err19 = {instancePath:instancePath+"/request/conversation",schemaPath:"#/$defs/FileRequest/oneOf/1/properties/conversation/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err19];
}
else {
vErrors.push(err19);
}
errors++;
}
var valid6 = _errs27 === errors;
}
else {
var valid6 = true;
}
if(valid6){
if(data3.id !== undefined){
const _errs29 = errors;
if(typeof data3.id !== "string"){
const err20 = {instancePath:instancePath+"/request/id",schemaPath:"#/$defs/FileRequest/oneOf/1/properties/id/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err20];
}
else {
vErrors.push(err20);
}
errors++;
}
var valid6 = _errs29 === errors;
}
else {
var valid6 = true;
}
if(valid6){
if(data3.name !== undefined){
const _errs31 = errors;
if(typeof data3.name !== "string"){
const err21 = {instancePath:instancePath+"/request/name",schemaPath:"#/$defs/FileRequest/oneOf/1/properties/name/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err21];
}
else {
vErrors.push(err21);
}
errors++;
}
var valid6 = _errs31 === errors;
}
else {
var valid6 = true;
}
if(valid6){
if(data3.size_bytes !== undefined){
const _errs33 = errors;
if(typeof data3.size_bytes !== "string"){
const err22 = {instancePath:instancePath+"/request/size_bytes",schemaPath:"#/$defs/FileRequest/oneOf/1/properties/size_bytes/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err22];
}
else {
vErrors.push(err22);
}
errors++;
}
var valid6 = _errs33 === errors;
}
else {
var valid6 = true;
}
}
}
}
}
}
}
}
else {
const err23 = {instancePath:instancePath+"/request",schemaPath:"#/$defs/FileRequest/oneOf/1/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err23];
}
else {
vErrors.push(err23);
}
errors++;
}
}
var _valid1 = _errs22 === errors;
if(_valid1 && valid4){
valid4 = false;
passing1 = [passing1, 1];
}
else {
if(_valid1){
valid4 = true;
passing1 = 1;
if(props2 !== true){
props2 = true;
}
}
const _errs35 = errors;
if(errors === _errs35){
if(data3 && typeof data3 == "object" && !Array.isArray(data3)){
let missing4;
if(((data3.action === undefined) && (missing4 = "action")) || ((data3.id === undefined) && (missing4 = "id"))){
const err24 = {instancePath:instancePath+"/request",schemaPath:"#/$defs/FileRequest/oneOf/2/required",keyword:"required",params:{missingProperty: missing4},message:"must have required property '"+missing4+"'"};
if(vErrors === null){
vErrors = [err24];
}
else {
vErrors.push(err24);
}
errors++;
}
else {
const _errs37 = errors;
for(const key4 in data3){
if(!((key4 === "action") || (key4 === "id"))){
const err25 = {instancePath:instancePath+"/request",schemaPath:"#/$defs/FileRequest/oneOf/2/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key4},message:"must NOT have additional properties"};
if(vErrors === null){
vErrors = [err25];
}
else {
vErrors.push(err25);
}
errors++;
break;
}
}
if(_errs37 === errors){
if(data3.action !== undefined){
let data11 = data3.action;
const _errs38 = errors;
if(typeof data11 !== "string"){
const err26 = {instancePath:instancePath+"/request/action",schemaPath:"#/$defs/FileRequest/oneOf/2/properties/action/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err26];
}
else {
vErrors.push(err26);
}
errors++;
}
if("commit" !== data11){
const err27 = {instancePath:instancePath+"/request/action",schemaPath:"#/$defs/FileRequest/oneOf/2/properties/action/const",keyword:"const",params:{allowedValue: "commit"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err27];
}
else {
vErrors.push(err27);
}
errors++;
}
var valid7 = _errs38 === errors;
}
else {
var valid7 = true;
}
if(valid7){
if(data3.id !== undefined){
const _errs40 = errors;
if(typeof data3.id !== "string"){
const err28 = {instancePath:instancePath+"/request/id",schemaPath:"#/$defs/FileRequest/oneOf/2/properties/id/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err28];
}
else {
vErrors.push(err28);
}
errors++;
}
var valid7 = _errs40 === errors;
}
else {
var valid7 = true;
}
}
}
}
}
else {
const err29 = {instancePath:instancePath+"/request",schemaPath:"#/$defs/FileRequest/oneOf/2/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err29];
}
else {
vErrors.push(err29);
}
errors++;
}
}
var _valid1 = _errs35 === errors;
if(_valid1 && valid4){
valid4 = false;
passing1 = [passing1, 2];
}
else {
if(_valid1){
valid4 = true;
passing1 = 2;
if(props2 !== true){
props2 = true;
}
}
const _errs42 = errors;
if(errors === _errs42){
if(data3 && typeof data3 == "object" && !Array.isArray(data3)){
let missing5;
if(((data3.action === undefined) && (missing5 = "action")) || ((data3.id === undefined) && (missing5 = "id"))){
const err30 = {instancePath:instancePath+"/request",schemaPath:"#/$defs/FileRequest/oneOf/3/required",keyword:"required",params:{missingProperty: missing5},message:"must have required property '"+missing5+"'"};
if(vErrors === null){
vErrors = [err30];
}
else {
vErrors.push(err30);
}
errors++;
}
else {
const _errs44 = errors;
for(const key5 in data3){
if(!((key5 === "action") || (key5 === "id"))){
const err31 = {instancePath:instancePath+"/request",schemaPath:"#/$defs/FileRequest/oneOf/3/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key5},message:"must NOT have additional properties"};
if(vErrors === null){
vErrors = [err31];
}
else {
vErrors.push(err31);
}
errors++;
break;
}
}
if(_errs44 === errors){
if(data3.action !== undefined){
let data13 = data3.action;
const _errs45 = errors;
if(typeof data13 !== "string"){
const err32 = {instancePath:instancePath+"/request/action",schemaPath:"#/$defs/FileRequest/oneOf/3/properties/action/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err32];
}
else {
vErrors.push(err32);
}
errors++;
}
if("accept" !== data13){
const err33 = {instancePath:instancePath+"/request/action",schemaPath:"#/$defs/FileRequest/oneOf/3/properties/action/const",keyword:"const",params:{allowedValue: "accept"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err33];
}
else {
vErrors.push(err33);
}
errors++;
}
var valid8 = _errs45 === errors;
}
else {
var valid8 = true;
}
if(valid8){
if(data3.id !== undefined){
const _errs47 = errors;
if(typeof data3.id !== "string"){
const err34 = {instancePath:instancePath+"/request/id",schemaPath:"#/$defs/FileRequest/oneOf/3/properties/id/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err34];
}
else {
vErrors.push(err34);
}
errors++;
}
var valid8 = _errs47 === errors;
}
else {
var valid8 = true;
}
}
}
}
}
else {
const err35 = {instancePath:instancePath+"/request",schemaPath:"#/$defs/FileRequest/oneOf/3/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err35];
}
else {
vErrors.push(err35);
}
errors++;
}
}
var _valid1 = _errs42 === errors;
if(_valid1 && valid4){
valid4 = false;
passing1 = [passing1, 3];
}
else {
if(_valid1){
valid4 = true;
passing1 = 3;
if(props2 !== true){
props2 = true;
}
}
const _errs49 = errors;
if(errors === _errs49){
if(data3 && typeof data3 == "object" && !Array.isArray(data3)){
let missing6;
if(((data3.action === undefined) && (missing6 = "action")) || ((data3.id === undefined) && (missing6 = "id"))){
const err36 = {instancePath:instancePath+"/request",schemaPath:"#/$defs/FileRequest/oneOf/4/required",keyword:"required",params:{missingProperty: missing6},message:"must have required property '"+missing6+"'"};
if(vErrors === null){
vErrors = [err36];
}
else {
vErrors.push(err36);
}
errors++;
}
else {
const _errs51 = errors;
for(const key6 in data3){
if(!((key6 === "action") || (key6 === "id"))){
const err37 = {instancePath:instancePath+"/request",schemaPath:"#/$defs/FileRequest/oneOf/4/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key6},message:"must NOT have additional properties"};
if(vErrors === null){
vErrors = [err37];
}
else {
vErrors.push(err37);
}
errors++;
break;
}
}
if(_errs51 === errors){
if(data3.action !== undefined){
let data15 = data3.action;
const _errs52 = errors;
if(typeof data15 !== "string"){
const err38 = {instancePath:instancePath+"/request/action",schemaPath:"#/$defs/FileRequest/oneOf/4/properties/action/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err38];
}
else {
vErrors.push(err38);
}
errors++;
}
if("pause" !== data15){
const err39 = {instancePath:instancePath+"/request/action",schemaPath:"#/$defs/FileRequest/oneOf/4/properties/action/const",keyword:"const",params:{allowedValue: "pause"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err39];
}
else {
vErrors.push(err39);
}
errors++;
}
var valid9 = _errs52 === errors;
}
else {
var valid9 = true;
}
if(valid9){
if(data3.id !== undefined){
const _errs54 = errors;
if(typeof data3.id !== "string"){
const err40 = {instancePath:instancePath+"/request/id",schemaPath:"#/$defs/FileRequest/oneOf/4/properties/id/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err40];
}
else {
vErrors.push(err40);
}
errors++;
}
var valid9 = _errs54 === errors;
}
else {
var valid9 = true;
}
}
}
}
}
else {
const err41 = {instancePath:instancePath+"/request",schemaPath:"#/$defs/FileRequest/oneOf/4/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err41];
}
else {
vErrors.push(err41);
}
errors++;
}
}
var _valid1 = _errs49 === errors;
if(_valid1 && valid4){
valid4 = false;
passing1 = [passing1, 4];
}
else {
if(_valid1){
valid4 = true;
passing1 = 4;
if(props2 !== true){
props2 = true;
}
}
const _errs56 = errors;
if(errors === _errs56){
if(data3 && typeof data3 == "object" && !Array.isArray(data3)){
let missing7;
if(((data3.action === undefined) && (missing7 = "action")) || ((data3.id === undefined) && (missing7 = "id"))){
const err42 = {instancePath:instancePath+"/request",schemaPath:"#/$defs/FileRequest/oneOf/5/required",keyword:"required",params:{missingProperty: missing7},message:"must have required property '"+missing7+"'"};
if(vErrors === null){
vErrors = [err42];
}
else {
vErrors.push(err42);
}
errors++;
}
else {
const _errs58 = errors;
for(const key7 in data3){
if(!((key7 === "action") || (key7 === "id"))){
const err43 = {instancePath:instancePath+"/request",schemaPath:"#/$defs/FileRequest/oneOf/5/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key7},message:"must NOT have additional properties"};
if(vErrors === null){
vErrors = [err43];
}
else {
vErrors.push(err43);
}
errors++;
break;
}
}
if(_errs58 === errors){
if(data3.action !== undefined){
let data17 = data3.action;
const _errs59 = errors;
if(typeof data17 !== "string"){
const err44 = {instancePath:instancePath+"/request/action",schemaPath:"#/$defs/FileRequest/oneOf/5/properties/action/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err44];
}
else {
vErrors.push(err44);
}
errors++;
}
if("resume" !== data17){
const err45 = {instancePath:instancePath+"/request/action",schemaPath:"#/$defs/FileRequest/oneOf/5/properties/action/const",keyword:"const",params:{allowedValue: "resume"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err45];
}
else {
vErrors.push(err45);
}
errors++;
}
var valid10 = _errs59 === errors;
}
else {
var valid10 = true;
}
if(valid10){
if(data3.id !== undefined){
const _errs61 = errors;
if(typeof data3.id !== "string"){
const err46 = {instancePath:instancePath+"/request/id",schemaPath:"#/$defs/FileRequest/oneOf/5/properties/id/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err46];
}
else {
vErrors.push(err46);
}
errors++;
}
var valid10 = _errs61 === errors;
}
else {
var valid10 = true;
}
}
}
}
}
else {
const err47 = {instancePath:instancePath+"/request",schemaPath:"#/$defs/FileRequest/oneOf/5/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err47];
}
else {
vErrors.push(err47);
}
errors++;
}
}
var _valid1 = _errs56 === errors;
if(_valid1 && valid4){
valid4 = false;
passing1 = [passing1, 5];
}
else {
if(_valid1){
valid4 = true;
passing1 = 5;
if(props2 !== true){
props2 = true;
}
}
const _errs63 = errors;
if(errors === _errs63){
if(data3 && typeof data3 == "object" && !Array.isArray(data3)){
let missing8;
if(((data3.action === undefined) && (missing8 = "action")) || ((data3.id === undefined) && (missing8 = "id"))){
const err48 = {instancePath:instancePath+"/request",schemaPath:"#/$defs/FileRequest/oneOf/6/required",keyword:"required",params:{missingProperty: missing8},message:"must have required property '"+missing8+"'"};
if(vErrors === null){
vErrors = [err48];
}
else {
vErrors.push(err48);
}
errors++;
}
else {
const _errs65 = errors;
for(const key8 in data3){
if(!((key8 === "action") || (key8 === "id"))){
const err49 = {instancePath:instancePath+"/request",schemaPath:"#/$defs/FileRequest/oneOf/6/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key8},message:"must NOT have additional properties"};
if(vErrors === null){
vErrors = [err49];
}
else {
vErrors.push(err49);
}
errors++;
break;
}
}
if(_errs65 === errors){
if(data3.action !== undefined){
let data19 = data3.action;
const _errs66 = errors;
if(typeof data19 !== "string"){
const err50 = {instancePath:instancePath+"/request/action",schemaPath:"#/$defs/FileRequest/oneOf/6/properties/action/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err50];
}
else {
vErrors.push(err50);
}
errors++;
}
if("cancel" !== data19){
const err51 = {instancePath:instancePath+"/request/action",schemaPath:"#/$defs/FileRequest/oneOf/6/properties/action/const",keyword:"const",params:{allowedValue: "cancel"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err51];
}
else {
vErrors.push(err51);
}
errors++;
}
var valid11 = _errs66 === errors;
}
else {
var valid11 = true;
}
if(valid11){
if(data3.id !== undefined){
const _errs68 = errors;
if(typeof data3.id !== "string"){
const err52 = {instancePath:instancePath+"/request/id",schemaPath:"#/$defs/FileRequest/oneOf/6/properties/id/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err52];
}
else {
vErrors.push(err52);
}
errors++;
}
var valid11 = _errs68 === errors;
}
else {
var valid11 = true;
}
}
}
}
}
else {
const err53 = {instancePath:instancePath+"/request",schemaPath:"#/$defs/FileRequest/oneOf/6/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err53];
}
else {
vErrors.push(err53);
}
errors++;
}
}
var _valid1 = _errs63 === errors;
if(_valid1 && valid4){
valid4 = false;
passing1 = [passing1, 6];
}
else {
if(_valid1){
valid4 = true;
passing1 = 6;
if(props2 !== true){
props2 = true;
}
}
const _errs70 = errors;
if(errors === _errs70){
if(data3 && typeof data3 == "object" && !Array.isArray(data3)){
let missing9;
if((((data3.action === undefined) && (missing9 = "action")) || ((data3.quota_bytes === undefined) && (missing9 = "quota_bytes"))) || ((data3.retention_days === undefined) && (missing9 = "retention_days"))){
const err54 = {instancePath:instancePath+"/request",schemaPath:"#/$defs/FileRequest/oneOf/7/required",keyword:"required",params:{missingProperty: missing9},message:"must have required property '"+missing9+"'"};
if(vErrors === null){
vErrors = [err54];
}
else {
vErrors.push(err54);
}
errors++;
}
else {
const _errs72 = errors;
for(const key9 in data3){
if(!(((key9 === "action") || (key9 === "quota_bytes")) || (key9 === "retention_days"))){
const err55 = {instancePath:instancePath+"/request",schemaPath:"#/$defs/FileRequest/oneOf/7/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key9},message:"must NOT have additional properties"};
if(vErrors === null){
vErrors = [err55];
}
else {
vErrors.push(err55);
}
errors++;
break;
}
}
if(_errs72 === errors){
if(data3.action !== undefined){
let data21 = data3.action;
const _errs73 = errors;
if(typeof data21 !== "string"){
const err56 = {instancePath:instancePath+"/request/action",schemaPath:"#/$defs/FileRequest/oneOf/7/properties/action/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err56];
}
else {
vErrors.push(err56);
}
errors++;
}
if("configure" !== data21){
const err57 = {instancePath:instancePath+"/request/action",schemaPath:"#/$defs/FileRequest/oneOf/7/properties/action/const",keyword:"const",params:{allowedValue: "configure"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err57];
}
else {
vErrors.push(err57);
}
errors++;
}
var valid12 = _errs73 === errors;
}
else {
var valid12 = true;
}
if(valid12){
if(data3.quota_bytes !== undefined){
const _errs75 = errors;
if(typeof data3.quota_bytes !== "string"){
const err58 = {instancePath:instancePath+"/request/quota_bytes",schemaPath:"#/$defs/FileRequest/oneOf/7/properties/quota_bytes/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err58];
}
else {
vErrors.push(err58);
}
errors++;
}
var valid12 = _errs75 === errors;
}
else {
var valid12 = true;
}
if(valid12){
if(data3.retention_days !== undefined){
let data23 = data3.retention_days;
const _errs77 = errors;
if(!(((typeof data23 == "number") && (!(data23 % 1) && !isNaN(data23))) && (isFinite(data23)))){
const err59 = {instancePath:instancePath+"/request/retention_days",schemaPath:"#/$defs/FileRequest/oneOf/7/properties/retention_days/type",keyword:"type",params:{type: "integer"},message:"must be integer"};
if(vErrors === null){
vErrors = [err59];
}
else {
vErrors.push(err59);
}
errors++;
}
if(errors === _errs77){
if((typeof data23 == "number") && (isFinite(data23))){
if(data23 > 65535 || isNaN(data23)){
const err60 = {instancePath:instancePath+"/request/retention_days",schemaPath:"#/$defs/FileRequest/oneOf/7/properties/retention_days/maximum",keyword:"maximum",params:{comparison: "<=", limit: 65535},message:"must be <= 65535"};
if(vErrors === null){
vErrors = [err60];
}
else {
vErrors.push(err60);
}
errors++;
}
else {
if(data23 < 0 || isNaN(data23)){
const err61 = {instancePath:instancePath+"/request/retention_days",schemaPath:"#/$defs/FileRequest/oneOf/7/properties/retention_days/minimum",keyword:"minimum",params:{comparison: ">=", limit: 0},message:"must be >= 0"};
if(vErrors === null){
vErrors = [err61];
}
else {
vErrors.push(err61);
}
errors++;
}
}
}
}
var valid12 = _errs77 === errors;
}
else {
var valid12 = true;
}
}
}
}
}
}
else {
const err62 = {instancePath:instancePath+"/request",schemaPath:"#/$defs/FileRequest/oneOf/7/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err62];
}
else {
vErrors.push(err62);
}
errors++;
}
}
var _valid1 = _errs70 === errors;
if(_valid1 && valid4){
valid4 = false;
passing1 = [passing1, 7];
}
else {
if(_valid1){
valid4 = true;
passing1 = 7;
if(props2 !== true){
props2 = true;
}
}
}
}
}
}
}
}
}
if(!valid4){
const err63 = {instancePath:instancePath+"/request",schemaPath:"#/$defs/FileRequest/oneOf",keyword:"oneOf",params:{passingSchemas: passing1},message:"must match exactly one schema in oneOf"};
if(vErrors === null){
vErrors = [err63];
}
else {
vErrors.push(err63);
}
errors++;
}
else {
errors = _errs14;
if(vErrors !== null){
if(_errs14){
vErrors.length = _errs14;
}
else {
vErrors = null;
}
}
}
var valid2 = _errs12 === errors;
}
else {
var valid2 = true;
}
}
}
}
}
else {
const err64 = {instancePath,schemaPath:"#/oneOf/1/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err64];
}
else {
vErrors.push(err64);
}
errors++;
}
}
var _valid0 = _errs7 === errors;
if(_valid0 && valid0){
valid0 = false;
passing0 = [passing0, 1];
}
else {
if(_valid0){
valid0 = true;
passing0 = 1;
if(props1 !== true){
props1 = true;
}
}
const _errs79 = errors;
if(errors === _errs79){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing10;
if((data.kind === undefined) && (missing10 = "kind")){
const err65 = {instancePath,schemaPath:"#/oneOf/2/required",keyword:"required",params:{missingProperty: missing10},message:"must have required property '"+missing10+"'"};
if(vErrors === null){
vErrors = [err65];
}
else {
vErrors.push(err65);
}
errors++;
}
else {
const _errs81 = errors;
for(const key10 in data){
if(!(key10 === "kind")){
const err66 = {instancePath,schemaPath:"#/oneOf/2/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key10},message:"must NOT have additional properties"};
if(vErrors === null){
vErrors = [err66];
}
else {
vErrors.push(err66);
}
errors++;
break;
}
}
if(_errs81 === errors){
if(data.kind !== undefined){
let data24 = data.kind;
if(typeof data24 !== "string"){
const err67 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/2/properties/kind/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err67];
}
else {
vErrors.push(err67);
}
errors++;
}
if("identify" !== data24){
const err68 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/2/properties/kind/const",keyword:"const",params:{allowedValue: "identify"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err68];
}
else {
vErrors.push(err68);
}
errors++;
}
}
}
}
}
else {
const err69 = {instancePath,schemaPath:"#/oneOf/2/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err69];
}
else {
vErrors.push(err69);
}
errors++;
}
}
var _valid0 = _errs79 === errors;
if(_valid0 && valid0){
valid0 = false;
passing0 = [passing0, 2];
}
else {
if(_valid0){
valid0 = true;
passing0 = 2;
if(props1 !== true){
props1 = true;
}
}
const _errs84 = errors;
if(errors === _errs84){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing11;
if((((data.kind === undefined) && (missing11 = "kind")) || ((data.passphrase === undefined) && (missing11 = "passphrase"))) || ((data.create === undefined) && (missing11 = "create"))){
const err70 = {instancePath,schemaPath:"#/oneOf/3/required",keyword:"required",params:{missingProperty: missing11},message:"must have required property '"+missing11+"'"};
if(vErrors === null){
vErrors = [err70];
}
else {
vErrors.push(err70);
}
errors++;
}
else {
const _errs86 = errors;
for(const key11 in data){
if(!(((key11 === "create") || (key11 === "kind")) || (key11 === "passphrase"))){
const err71 = {instancePath,schemaPath:"#/oneOf/3/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key11},message:"must NOT have additional properties"};
if(vErrors === null){
vErrors = [err71];
}
else {
vErrors.push(err71);
}
errors++;
break;
}
}
if(_errs86 === errors){
if(data.create !== undefined){
const _errs87 = errors;
if(typeof data.create !== "boolean"){
const err72 = {instancePath:instancePath+"/create",schemaPath:"#/oneOf/3/properties/create/type",keyword:"type",params:{type: "boolean"},message:"must be boolean"};
if(vErrors === null){
vErrors = [err72];
}
else {
vErrors.push(err72);
}
errors++;
}
var valid14 = _errs87 === errors;
}
else {
var valid14 = true;
}
if(valid14){
if(data.kind !== undefined){
let data26 = data.kind;
const _errs89 = errors;
if(typeof data26 !== "string"){
const err73 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/3/properties/kind/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err73];
}
else {
vErrors.push(err73);
}
errors++;
}
if("unlock" !== data26){
const err74 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/3/properties/kind/const",keyword:"const",params:{allowedValue: "unlock"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err74];
}
else {
vErrors.push(err74);
}
errors++;
}
var valid14 = _errs89 === errors;
}
else {
var valid14 = true;
}
if(valid14){
if(data.passphrase !== undefined){
const _errs91 = errors;
if(typeof data.passphrase !== "string"){
const err75 = {instancePath:instancePath+"/passphrase",schemaPath:"#/oneOf/3/properties/passphrase/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err75];
}
else {
vErrors.push(err75);
}
errors++;
}
var valid14 = _errs91 === errors;
}
else {
var valid14 = true;
}
}
}
}
}
}
else {
const err76 = {instancePath,schemaPath:"#/oneOf/3/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err76];
}
else {
vErrors.push(err76);
}
errors++;
}
}
var _valid0 = _errs84 === errors;
if(_valid0 && valid0){
valid0 = false;
passing0 = [passing0, 3];
}
else {
if(_valid0){
valid0 = true;
passing0 = 3;
if(props1 !== true){
props1 = true;
}
}
const _errs93 = errors;
if(errors === _errs93){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing12;
if((data.kind === undefined) && (missing12 = "kind")){
const err77 = {instancePath,schemaPath:"#/oneOf/4/required",keyword:"required",params:{missingProperty: missing12},message:"must have required property '"+missing12+"'"};
if(vErrors === null){
vErrors = [err77];
}
else {
vErrors.push(err77);
}
errors++;
}
else {
const _errs95 = errors;
for(const key12 in data){
if(!(key12 === "kind")){
const err78 = {instancePath,schemaPath:"#/oneOf/4/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key12},message:"must NOT have additional properties"};
if(vErrors === null){
vErrors = [err78];
}
else {
vErrors.push(err78);
}
errors++;
break;
}
}
if(_errs95 === errors){
if(data.kind !== undefined){
let data28 = data.kind;
if(typeof data28 !== "string"){
const err79 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/4/properties/kind/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err79];
}
else {
vErrors.push(err79);
}
errors++;
}
if("lock" !== data28){
const err80 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/4/properties/kind/const",keyword:"const",params:{allowedValue: "lock"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err80];
}
else {
vErrors.push(err80);
}
errors++;
}
}
}
}
}
else {
const err81 = {instancePath,schemaPath:"#/oneOf/4/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err81];
}
else {
vErrors.push(err81);
}
errors++;
}
}
var _valid0 = _errs93 === errors;
if(_valid0 && valid0){
valid0 = false;
passing0 = [passing0, 4];
}
else {
if(_valid0){
valid0 = true;
passing0 = 4;
if(props1 !== true){
props1 = true;
}
}
const _errs98 = errors;
if(errors === _errs98){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing13;
if((data.kind === undefined) && (missing13 = "kind")){
const err82 = {instancePath,schemaPath:"#/oneOf/5/required",keyword:"required",params:{missingProperty: missing13},message:"must have required property '"+missing13+"'"};
if(vErrors === null){
vErrors = [err82];
}
else {
vErrors.push(err82);
}
errors++;
}
else {
const _errs100 = errors;
for(const key13 in data){
if(!(key13 === "kind")){
const err83 = {instancePath,schemaPath:"#/oneOf/5/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key13},message:"must NOT have additional properties"};
if(vErrors === null){
vErrors = [err83];
}
else {
vErrors.push(err83);
}
errors++;
break;
}
}
if(_errs100 === errors){
if(data.kind !== undefined){
let data29 = data.kind;
if(typeof data29 !== "string"){
const err84 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/5/properties/kind/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err84];
}
else {
vErrors.push(err84);
}
errors++;
}
if("disconnect" !== data29){
const err85 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/5/properties/kind/const",keyword:"const",params:{allowedValue: "disconnect"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err85];
}
else {
vErrors.push(err85);
}
errors++;
}
}
}
}
}
else {
const err86 = {instancePath,schemaPath:"#/oneOf/5/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err86];
}
else {
vErrors.push(err86);
}
errors++;
}
}
var _valid0 = _errs98 === errors;
if(_valid0 && valid0){
valid0 = false;
passing0 = [passing0, 5];
}
else {
if(_valid0){
valid0 = true;
passing0 = 5;
if(props1 !== true){
props1 = true;
}
}
const _errs103 = errors;
if(errors === _errs103){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing14;
if((data.kind === undefined) && (missing14 = "kind")){
const err87 = {instancePath,schemaPath:"#/oneOf/6/required",keyword:"required",params:{missingProperty: missing14},message:"must have required property '"+missing14+"'"};
if(vErrors === null){
vErrors = [err87];
}
else {
vErrors.push(err87);
}
errors++;
}
else {
const _errs105 = errors;
for(const key14 in data){
if(!(key14 === "kind")){
const err88 = {instancePath,schemaPath:"#/oneOf/6/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key14},message:"must NOT have additional properties"};
if(vErrors === null){
vErrors = [err88];
}
else {
vErrors.push(err88);
}
errors++;
break;
}
}
if(_errs105 === errors){
if(data.kind !== undefined){
let data30 = data.kind;
if(typeof data30 !== "string"){
const err89 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/6/properties/kind/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err89];
}
else {
vErrors.push(err89);
}
errors++;
}
if("snapshot" !== data30){
const err90 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/6/properties/kind/const",keyword:"const",params:{allowedValue: "snapshot"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err90];
}
else {
vErrors.push(err90);
}
errors++;
}
}
}
}
}
else {
const err91 = {instancePath,schemaPath:"#/oneOf/6/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err91];
}
else {
vErrors.push(err91);
}
errors++;
}
}
var _valid0 = _errs103 === errors;
if(_valid0 && valid0){
valid0 = false;
passing0 = [passing0, 6];
}
else {
if(_valid0){
valid0 = true;
passing0 = 6;
if(props1 !== true){
props1 = true;
}
}
const _errs108 = errors;
if(errors === _errs108){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing15;
if((data.kind === undefined) && (missing15 = "kind")){
const err92 = {instancePath,schemaPath:"#/oneOf/7/required",keyword:"required",params:{missingProperty: missing15},message:"must have required property '"+missing15+"'"};
if(vErrors === null){
vErrors = [err92];
}
else {
vErrors.push(err92);
}
errors++;
}
else {
const _errs110 = errors;
for(const key15 in data){
if(!(key15 === "kind")){
const err93 = {instancePath,schemaPath:"#/oneOf/7/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key15},message:"must NOT have additional properties"};
if(vErrors === null){
vErrors = [err93];
}
else {
vErrors.push(err93);
}
errors++;
break;
}
}
if(_errs110 === errors){
if(data.kind !== undefined){
let data31 = data.kind;
if(typeof data31 !== "string"){
const err94 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/7/properties/kind/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err94];
}
else {
vErrors.push(err94);
}
errors++;
}
if("network_status" !== data31){
const err95 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/7/properties/kind/const",keyword:"const",params:{allowedValue: "network_status"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err95];
}
else {
vErrors.push(err95);
}
errors++;
}
}
}
}
}
else {
const err96 = {instancePath,schemaPath:"#/oneOf/7/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err96];
}
else {
vErrors.push(err96);
}
errors++;
}
}
var _valid0 = _errs108 === errors;
if(_valid0 && valid0){
valid0 = false;
passing0 = [passing0, 7];
}
else {
if(_valid0){
valid0 = true;
passing0 = 7;
if(props1 !== true){
props1 = true;
}
}
const _errs113 = errors;
if(errors === _errs113){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing16;
if(((data.kind === undefined) && (missing16 = "kind")) || ((data.code === undefined) && (missing16 = "code"))){
const err97 = {instancePath,schemaPath:"#/oneOf/8/required",keyword:"required",params:{missingProperty: missing16},message:"must have required property '"+missing16+"'"};
if(vErrors === null){
vErrors = [err97];
}
else {
vErrors.push(err97);
}
errors++;
}
else {
const _errs115 = errors;
for(const key16 in data){
if(!((key16 === "code") || (key16 === "kind"))){
const err98 = {instancePath,schemaPath:"#/oneOf/8/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key16},message:"must NOT have additional properties"};
if(vErrors === null){
vErrors = [err98];
}
else {
vErrors.push(err98);
}
errors++;
break;
}
}
if(_errs115 === errors){
if(data.code !== undefined){
const _errs116 = errors;
if(typeof data.code !== "string"){
const err99 = {instancePath:instancePath+"/code",schemaPath:"#/oneOf/8/properties/code/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err99];
}
else {
vErrors.push(err99);
}
errors++;
}
var valid19 = _errs116 === errors;
}
else {
var valid19 = true;
}
if(valid19){
if(data.kind !== undefined){
let data33 = data.kind;
const _errs118 = errors;
if(typeof data33 !== "string"){
const err100 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/8/properties/kind/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err100];
}
else {
vErrors.push(err100);
}
errors++;
}
if("import_network_invitation" !== data33){
const err101 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/8/properties/kind/const",keyword:"const",params:{allowedValue: "import_network_invitation"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err101];
}
else {
vErrors.push(err101);
}
errors++;
}
var valid19 = _errs118 === errors;
}
else {
var valid19 = true;
}
}
}
}
}
else {
const err102 = {instancePath,schemaPath:"#/oneOf/8/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err102];
}
else {
vErrors.push(err102);
}
errors++;
}
}
var _valid0 = _errs113 === errors;
if(_valid0 && valid0){
valid0 = false;
passing0 = [passing0, 8];
}
else {
if(_valid0){
valid0 = true;
passing0 = 8;
if(props1 !== true){
props1 = true;
}
}
const _errs120 = errors;
if(errors === _errs120){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing17;
if((data.kind === undefined) && (missing17 = "kind")){
const err103 = {instancePath,schemaPath:"#/oneOf/9/required",keyword:"required",params:{missingProperty: missing17},message:"must have required property '"+missing17+"'"};
if(vErrors === null){
vErrors = [err103];
}
else {
vErrors.push(err103);
}
errors++;
}
else {
const _errs122 = errors;
for(const key17 in data){
if(!((key17 === "conversation") || (key17 === "kind"))){
const err104 = {instancePath,schemaPath:"#/oneOf/9/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key17},message:"must NOT have additional properties"};
if(vErrors === null){
vErrors = [err104];
}
else {
vErrors.push(err104);
}
errors++;
break;
}
}
if(_errs122 === errors){
if(data.conversation !== undefined){
let data34 = data.conversation;
const _errs123 = errors;
if((typeof data34 !== "string") && (data34 !== null)){
const err105 = {instancePath:instancePath+"/conversation",schemaPath:"#/oneOf/9/properties/conversation/type",keyword:"type",params:{type: schema68.oneOf[9].properties.conversation.type},message:"must be string,null"};
if(vErrors === null){
vErrors = [err105];
}
else {
vErrors.push(err105);
}
errors++;
}
var valid20 = _errs123 === errors;
}
else {
var valid20 = true;
}
if(valid20){
if(data.kind !== undefined){
let data35 = data.kind;
const _errs125 = errors;
if(typeof data35 !== "string"){
const err106 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/9/properties/kind/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err106];
}
else {
vErrors.push(err106);
}
errors++;
}
if("catalogue" !== data35){
const err107 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/9/properties/kind/const",keyword:"const",params:{allowedValue: "catalogue"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err107];
}
else {
vErrors.push(err107);
}
errors++;
}
var valid20 = _errs125 === errors;
}
else {
var valid20 = true;
}
}
}
}
}
else {
const err108 = {instancePath,schemaPath:"#/oneOf/9/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err108];
}
else {
vErrors.push(err108);
}
errors++;
}
}
var _valid0 = _errs120 === errors;
if(_valid0 && valid0){
valid0 = false;
passing0 = [passing0, 9];
}
else {
if(_valid0){
valid0 = true;
passing0 = 9;
if(props1 !== true){
props1 = true;
}
}
const _errs127 = errors;
if(errors === _errs127){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing18;
if((((data.kind === undefined) && (missing18 = "kind")) || ((data.conversation === undefined) && (missing18 = "conversation"))) || ((data.limit === undefined) && (missing18 = "limit"))){
const err109 = {instancePath,schemaPath:"#/oneOf/10/required",keyword:"required",params:{missingProperty: missing18},message:"must have required property '"+missing18+"'"};
if(vErrors === null){
vErrors = [err109];
}
else {
vErrors.push(err109);
}
errors++;
}
else {
const _errs129 = errors;
for(const key18 in data){
if(!((((key18 === "before") || (key18 === "conversation")) || (key18 === "kind")) || (key18 === "limit"))){
const err110 = {instancePath,schemaPath:"#/oneOf/10/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key18},message:"must NOT have additional properties"};
if(vErrors === null){
vErrors = [err110];
}
else {
vErrors.push(err110);
}
errors++;
break;
}
}
if(_errs129 === errors){
if(data.before !== undefined){
let data36 = data.before;
const _errs130 = errors;
if((typeof data36 !== "string") && (data36 !== null)){
const err111 = {instancePath:instancePath+"/before",schemaPath:"#/oneOf/10/properties/before/type",keyword:"type",params:{type: schema68.oneOf[10].properties.before.type},message:"must be string,null"};
if(vErrors === null){
vErrors = [err111];
}
else {
vErrors.push(err111);
}
errors++;
}
var valid21 = _errs130 === errors;
}
else {
var valid21 = true;
}
if(valid21){
if(data.conversation !== undefined){
const _errs132 = errors;
if(typeof data.conversation !== "string"){
const err112 = {instancePath:instancePath+"/conversation",schemaPath:"#/oneOf/10/properties/conversation/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err112];
}
else {
vErrors.push(err112);
}
errors++;
}
var valid21 = _errs132 === errors;
}
else {
var valid21 = true;
}
if(valid21){
if(data.kind !== undefined){
let data38 = data.kind;
const _errs134 = errors;
if(typeof data38 !== "string"){
const err113 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/10/properties/kind/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err113];
}
else {
vErrors.push(err113);
}
errors++;
}
if("history" !== data38){
const err114 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/10/properties/kind/const",keyword:"const",params:{allowedValue: "history"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err114];
}
else {
vErrors.push(err114);
}
errors++;
}
var valid21 = _errs134 === errors;
}
else {
var valid21 = true;
}
if(valid21){
if(data.limit !== undefined){
let data39 = data.limit;
const _errs136 = errors;
if(!(((typeof data39 == "number") && (!(data39 % 1) && !isNaN(data39))) && (isFinite(data39)))){
const err115 = {instancePath:instancePath+"/limit",schemaPath:"#/oneOf/10/properties/limit/type",keyword:"type",params:{type: "integer"},message:"must be integer"};
if(vErrors === null){
vErrors = [err115];
}
else {
vErrors.push(err115);
}
errors++;
}
if(errors === _errs136){
if((typeof data39 == "number") && (isFinite(data39))){
if(data39 > 65535 || isNaN(data39)){
const err116 = {instancePath:instancePath+"/limit",schemaPath:"#/oneOf/10/properties/limit/maximum",keyword:"maximum",params:{comparison: "<=", limit: 65535},message:"must be <= 65535"};
if(vErrors === null){
vErrors = [err116];
}
else {
vErrors.push(err116);
}
errors++;
}
else {
if(data39 < 0 || isNaN(data39)){
const err117 = {instancePath:instancePath+"/limit",schemaPath:"#/oneOf/10/properties/limit/minimum",keyword:"minimum",params:{comparison: ">=", limit: 0},message:"must be >= 0"};
if(vErrors === null){
vErrors = [err117];
}
else {
vErrors.push(err117);
}
errors++;
}
}
}
}
var valid21 = _errs136 === errors;
}
else {
var valid21 = true;
}
}
}
}
}
}
}
else {
const err118 = {instancePath,schemaPath:"#/oneOf/10/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err118];
}
else {
vErrors.push(err118);
}
errors++;
}
}
var _valid0 = _errs127 === errors;
if(_valid0 && valid0){
valid0 = false;
passing0 = [passing0, 10];
}
else {
if(_valid0){
valid0 = true;
passing0 = 10;
if(props1 !== true){
props1 = true;
}
}
const _errs138 = errors;
if(errors === _errs138){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing19;
if(((((data.kind === undefined) && (missing19 = "kind")) || ((data.conversation === undefined) && (missing19 = "conversation"))) || ((data.text === undefined) && (missing19 = "text"))) || ((data.limit === undefined) && (missing19 = "limit"))){
const err119 = {instancePath,schemaPath:"#/oneOf/11/required",keyword:"required",params:{missingProperty: missing19},message:"must have required property '"+missing19+"'"};
if(vErrors === null){
vErrors = [err119];
}
else {
vErrors.push(err119);
}
errors++;
}
else {
const _errs140 = errors;
for(const key19 in data){
if(!(((((key19 === "before") || (key19 === "conversation")) || (key19 === "kind")) || (key19 === "limit")) || (key19 === "text"))){
const err120 = {instancePath,schemaPath:"#/oneOf/11/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key19},message:"must NOT have additional properties"};
if(vErrors === null){
vErrors = [err120];
}
else {
vErrors.push(err120);
}
errors++;
break;
}
}
if(_errs140 === errors){
if(data.before !== undefined){
let data40 = data.before;
const _errs141 = errors;
if((typeof data40 !== "string") && (data40 !== null)){
const err121 = {instancePath:instancePath+"/before",schemaPath:"#/oneOf/11/properties/before/type",keyword:"type",params:{type: schema68.oneOf[11].properties.before.type},message:"must be string,null"};
if(vErrors === null){
vErrors = [err121];
}
else {
vErrors.push(err121);
}
errors++;
}
var valid22 = _errs141 === errors;
}
else {
var valid22 = true;
}
if(valid22){
if(data.conversation !== undefined){
const _errs143 = errors;
if(typeof data.conversation !== "string"){
const err122 = {instancePath:instancePath+"/conversation",schemaPath:"#/oneOf/11/properties/conversation/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err122];
}
else {
vErrors.push(err122);
}
errors++;
}
var valid22 = _errs143 === errors;
}
else {
var valid22 = true;
}
if(valid22){
if(data.kind !== undefined){
let data42 = data.kind;
const _errs145 = errors;
if(typeof data42 !== "string"){
const err123 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/11/properties/kind/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err123];
}
else {
vErrors.push(err123);
}
errors++;
}
if("search" !== data42){
const err124 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/11/properties/kind/const",keyword:"const",params:{allowedValue: "search"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err124];
}
else {
vErrors.push(err124);
}
errors++;
}
var valid22 = _errs145 === errors;
}
else {
var valid22 = true;
}
if(valid22){
if(data.limit !== undefined){
let data43 = data.limit;
const _errs147 = errors;
if(!(((typeof data43 == "number") && (!(data43 % 1) && !isNaN(data43))) && (isFinite(data43)))){
const err125 = {instancePath:instancePath+"/limit",schemaPath:"#/oneOf/11/properties/limit/type",keyword:"type",params:{type: "integer"},message:"must be integer"};
if(vErrors === null){
vErrors = [err125];
}
else {
vErrors.push(err125);
}
errors++;
}
if(errors === _errs147){
if((typeof data43 == "number") && (isFinite(data43))){
if(data43 > 65535 || isNaN(data43)){
const err126 = {instancePath:instancePath+"/limit",schemaPath:"#/oneOf/11/properties/limit/maximum",keyword:"maximum",params:{comparison: "<=", limit: 65535},message:"must be <= 65535"};
if(vErrors === null){
vErrors = [err126];
}
else {
vErrors.push(err126);
}
errors++;
}
else {
if(data43 < 0 || isNaN(data43)){
const err127 = {instancePath:instancePath+"/limit",schemaPath:"#/oneOf/11/properties/limit/minimum",keyword:"minimum",params:{comparison: ">=", limit: 0},message:"must be >= 0"};
if(vErrors === null){
vErrors = [err127];
}
else {
vErrors.push(err127);
}
errors++;
}
}
}
}
var valid22 = _errs147 === errors;
}
else {
var valid22 = true;
}
if(valid22){
if(data.text !== undefined){
const _errs149 = errors;
if(typeof data.text !== "string"){
const err128 = {instancePath:instancePath+"/text",schemaPath:"#/oneOf/11/properties/text/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err128];
}
else {
vErrors.push(err128);
}
errors++;
}
var valid22 = _errs149 === errors;
}
else {
var valid22 = true;
}
}
}
}
}
}
}
}
else {
const err129 = {instancePath,schemaPath:"#/oneOf/11/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err129];
}
else {
vErrors.push(err129);
}
errors++;
}
}
var _valid0 = _errs138 === errors;
if(_valid0 && valid0){
valid0 = false;
passing0 = [passing0, 11];
}
else {
if(_valid0){
valid0 = true;
passing0 = 11;
if(props1 !== true){
props1 = true;
}
}
const _errs151 = errors;
if(errors === _errs151){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing20;
if((((data.kind === undefined) && (missing20 = "kind")) || ((data.operation_id === undefined) && (missing20 = "operation_id"))) || ((data.text === undefined) && (missing20 = "text"))){
const err130 = {instancePath,schemaPath:"#/oneOf/12/required",keyword:"required",params:{missingProperty: missing20},message:"must have required property '"+missing20+"'"};
if(vErrors === null){
vErrors = [err130];
}
else {
vErrors.push(err130);
}
errors++;
}
else {
const _errs153 = errors;
for(const key20 in data){
if(!((((key20 === "conversation") || (key20 === "kind")) || (key20 === "operation_id")) || (key20 === "text"))){
const err131 = {instancePath,schemaPath:"#/oneOf/12/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key20},message:"must NOT have additional properties"};
if(vErrors === null){
vErrors = [err131];
}
else {
vErrors.push(err131);
}
errors++;
break;
}
}
if(_errs153 === errors){
if(data.conversation !== undefined){
let data45 = data.conversation;
const _errs154 = errors;
if((typeof data45 !== "string") && (data45 !== null)){
const err132 = {instancePath:instancePath+"/conversation",schemaPath:"#/oneOf/12/properties/conversation/type",keyword:"type",params:{type: schema68.oneOf[12].properties.conversation.type},message:"must be string,null"};
if(vErrors === null){
vErrors = [err132];
}
else {
vErrors.push(err132);
}
errors++;
}
var valid23 = _errs154 === errors;
}
else {
var valid23 = true;
}
if(valid23){
if(data.kind !== undefined){
let data46 = data.kind;
const _errs156 = errors;
if(typeof data46 !== "string"){
const err133 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/12/properties/kind/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err133];
}
else {
vErrors.push(err133);
}
errors++;
}
if("submit" !== data46){
const err134 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/12/properties/kind/const",keyword:"const",params:{allowedValue: "submit"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err134];
}
else {
vErrors.push(err134);
}
errors++;
}
var valid23 = _errs156 === errors;
}
else {
var valid23 = true;
}
if(valid23){
if(data.operation_id !== undefined){
const _errs158 = errors;
if(typeof data.operation_id !== "string"){
const err135 = {instancePath:instancePath+"/operation_id",schemaPath:"#/oneOf/12/properties/operation_id/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err135];
}
else {
vErrors.push(err135);
}
errors++;
}
var valid23 = _errs158 === errors;
}
else {
var valid23 = true;
}
if(valid23){
if(data.text !== undefined){
const _errs160 = errors;
if(typeof data.text !== "string"){
const err136 = {instancePath:instancePath+"/text",schemaPath:"#/oneOf/12/properties/text/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err136];
}
else {
vErrors.push(err136);
}
errors++;
}
var valid23 = _errs160 === errors;
}
else {
var valid23 = true;
}
}
}
}
}
}
}
else {
const err137 = {instancePath,schemaPath:"#/oneOf/12/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err137];
}
else {
vErrors.push(err137);
}
errors++;
}
}
var _valid0 = _errs151 === errors;
if(_valid0 && valid0){
valid0 = false;
passing0 = [passing0, 12];
}
else {
if(_valid0){
valid0 = true;
passing0 = 12;
if(props1 !== true){
props1 = true;
}
}
const _errs162 = errors;
if(errors === _errs162){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing21;
if(((data.kind === undefined) && (missing21 = "kind")) || ((data.text === undefined) && (missing21 = "text"))){
const err138 = {instancePath,schemaPath:"#/oneOf/13/required",keyword:"required",params:{missingProperty: missing21},message:"must have required property '"+missing21+"'"};
if(vErrors === null){
vErrors = [err138];
}
else {
vErrors.push(err138);
}
errors++;
}
else {
const _errs164 = errors;
for(const key21 in data){
if(!(((key21 === "conversation") || (key21 === "kind")) || (key21 === "text"))){
const err139 = {instancePath,schemaPath:"#/oneOf/13/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key21},message:"must NOT have additional properties"};
if(vErrors === null){
vErrors = [err139];
}
else {
vErrors.push(err139);
}
errors++;
break;
}
}
if(_errs164 === errors){
if(data.conversation !== undefined){
let data49 = data.conversation;
const _errs165 = errors;
if((typeof data49 !== "string") && (data49 !== null)){
const err140 = {instancePath:instancePath+"/conversation",schemaPath:"#/oneOf/13/properties/conversation/type",keyword:"type",params:{type: schema68.oneOf[13].properties.conversation.type},message:"must be string,null"};
if(vErrors === null){
vErrors = [err140];
}
else {
vErrors.push(err140);
}
errors++;
}
var valid24 = _errs165 === errors;
}
else {
var valid24 = true;
}
if(valid24){
if(data.kind !== undefined){
let data50 = data.kind;
const _errs167 = errors;
if(typeof data50 !== "string"){
const err141 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/13/properties/kind/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err141];
}
else {
vErrors.push(err141);
}
errors++;
}
if("complete" !== data50){
const err142 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/13/properties/kind/const",keyword:"const",params:{allowedValue: "complete"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err142];
}
else {
vErrors.push(err142);
}
errors++;
}
var valid24 = _errs167 === errors;
}
else {
var valid24 = true;
}
if(valid24){
if(data.text !== undefined){
const _errs169 = errors;
if(typeof data.text !== "string"){
const err143 = {instancePath:instancePath+"/text",schemaPath:"#/oneOf/13/properties/text/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err143];
}
else {
vErrors.push(err143);
}
errors++;
}
var valid24 = _errs169 === errors;
}
else {
var valid24 = true;
}
}
}
}
}
}
else {
const err144 = {instancePath,schemaPath:"#/oneOf/13/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err144];
}
else {
vErrors.push(err144);
}
errors++;
}
}
var _valid0 = _errs162 === errors;
if(_valid0 && valid0){
valid0 = false;
passing0 = [passing0, 13];
}
else {
if(_valid0){
valid0 = true;
passing0 = 13;
if(props1 !== true){
props1 = true;
}
}
const _errs171 = errors;
if(errors === _errs171){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing22;
if((((data.kind === undefined) && (missing22 = "kind")) || ((data.conversation === undefined) && (missing22 = "conversation"))) || ((data.message_id === undefined) && (missing22 = "message_id"))){
const err145 = {instancePath,schemaPath:"#/oneOf/14/required",keyword:"required",params:{missingProperty: missing22},message:"must have required property '"+missing22+"'"};
if(vErrors === null){
vErrors = [err145];
}
else {
vErrors.push(err145);
}
errors++;
}
else {
const _errs173 = errors;
for(const key22 in data){
if(!(((key22 === "conversation") || (key22 === "kind")) || (key22 === "message_id"))){
const err146 = {instancePath,schemaPath:"#/oneOf/14/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key22},message:"must NOT have additional properties"};
if(vErrors === null){
vErrors = [err146];
}
else {
vErrors.push(err146);
}
errors++;
break;
}
}
if(_errs173 === errors){
if(data.conversation !== undefined){
const _errs174 = errors;
if(typeof data.conversation !== "string"){
const err147 = {instancePath:instancePath+"/conversation",schemaPath:"#/oneOf/14/properties/conversation/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err147];
}
else {
vErrors.push(err147);
}
errors++;
}
var valid25 = _errs174 === errors;
}
else {
var valid25 = true;
}
if(valid25){
if(data.kind !== undefined){
let data53 = data.kind;
const _errs176 = errors;
if(typeof data53 !== "string"){
const err148 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/14/properties/kind/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err148];
}
else {
vErrors.push(err148);
}
errors++;
}
if("mark_read" !== data53){
const err149 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/14/properties/kind/const",keyword:"const",params:{allowedValue: "mark_read"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err149];
}
else {
vErrors.push(err149);
}
errors++;
}
var valid25 = _errs176 === errors;
}
else {
var valid25 = true;
}
if(valid25){
if(data.message_id !== undefined){
const _errs178 = errors;
if(typeof data.message_id !== "string"){
const err150 = {instancePath:instancePath+"/message_id",schemaPath:"#/oneOf/14/properties/message_id/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err150];
}
else {
vErrors.push(err150);
}
errors++;
}
var valid25 = _errs178 === errors;
}
else {
var valid25 = true;
}
}
}
}
}
}
else {
const err151 = {instancePath,schemaPath:"#/oneOf/14/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err151];
}
else {
vErrors.push(err151);
}
errors++;
}
}
var _valid0 = _errs171 === errors;
if(_valid0 && valid0){
valid0 = false;
passing0 = [passing0, 14];
}
else {
if(_valid0){
valid0 = true;
passing0 = 14;
if(props1 !== true){
props1 = true;
}
}
const _errs180 = errors;
if(errors === _errs180){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing23;
if((((data.kind === undefined) && (missing23 = "kind")) || ((data.after === undefined) && (missing23 = "after"))) || ((data.wait_ms === undefined) && (missing23 = "wait_ms"))){
const err152 = {instancePath,schemaPath:"#/oneOf/15/required",keyword:"required",params:{missingProperty: missing23},message:"must have required property '"+missing23+"'"};
if(vErrors === null){
vErrors = [err152];
}
else {
vErrors.push(err152);
}
errors++;
}
else {
const _errs182 = errors;
for(const key23 in data){
if(!(((key23 === "after") || (key23 === "kind")) || (key23 === "wait_ms"))){
const err153 = {instancePath,schemaPath:"#/oneOf/15/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key23},message:"must NOT have additional properties"};
if(vErrors === null){
vErrors = [err153];
}
else {
vErrors.push(err153);
}
errors++;
break;
}
}
if(_errs182 === errors){
if(data.after !== undefined){
const _errs183 = errors;
if(typeof data.after !== "string"){
const err154 = {instancePath:instancePath+"/after",schemaPath:"#/oneOf/15/properties/after/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err154];
}
else {
vErrors.push(err154);
}
errors++;
}
var valid26 = _errs183 === errors;
}
else {
var valid26 = true;
}
if(valid26){
if(data.kind !== undefined){
let data56 = data.kind;
const _errs185 = errors;
if(typeof data56 !== "string"){
const err155 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/15/properties/kind/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err155];
}
else {
vErrors.push(err155);
}
errors++;
}
if("events" !== data56){
const err156 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/15/properties/kind/const",keyword:"const",params:{allowedValue: "events"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err156];
}
else {
vErrors.push(err156);
}
errors++;
}
var valid26 = _errs185 === errors;
}
else {
var valid26 = true;
}
if(valid26){
if(data.wait_ms !== undefined){
let data57 = data.wait_ms;
const _errs187 = errors;
if(!(((typeof data57 == "number") && (!(data57 % 1) && !isNaN(data57))) && (isFinite(data57)))){
const err157 = {instancePath:instancePath+"/wait_ms",schemaPath:"#/oneOf/15/properties/wait_ms/type",keyword:"type",params:{type: "integer"},message:"must be integer"};
if(vErrors === null){
vErrors = [err157];
}
else {
vErrors.push(err157);
}
errors++;
}
if(errors === _errs187){
if((typeof data57 == "number") && (isFinite(data57))){
if(data57 > 65535 || isNaN(data57)){
const err158 = {instancePath:instancePath+"/wait_ms",schemaPath:"#/oneOf/15/properties/wait_ms/maximum",keyword:"maximum",params:{comparison: "<=", limit: 65535},message:"must be <= 65535"};
if(vErrors === null){
vErrors = [err158];
}
else {
vErrors.push(err158);
}
errors++;
}
else {
if(data57 < 0 || isNaN(data57)){
const err159 = {instancePath:instancePath+"/wait_ms",schemaPath:"#/oneOf/15/properties/wait_ms/minimum",keyword:"minimum",params:{comparison: ">=", limit: 0},message:"must be >= 0"};
if(vErrors === null){
vErrors = [err159];
}
else {
vErrors.push(err159);
}
errors++;
}
}
}
}
var valid26 = _errs187 === errors;
}
else {
var valid26 = true;
}
}
}
}
}
}
else {
const err160 = {instancePath,schemaPath:"#/oneOf/15/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err160];
}
else {
vErrors.push(err160);
}
errors++;
}
}
var _valid0 = _errs180 === errors;
if(_valid0 && valid0){
valid0 = false;
passing0 = [passing0, 15];
}
else {
if(_valid0){
valid0 = true;
passing0 = 15;
if(props1 !== true){
props1 = true;
}
}
}
}
}
}
}
}
}
}
}
}
}
}
}
}
}
if(!valid0){
const err161 = {instancePath,schemaPath:"#/oneOf",keyword:"oneOf",params:{passingSchemas: passing0},message:"must match exactly one schema in oneOf"};
if(vErrors === null){
vErrors = [err161];
}
else {
vErrors.push(err161);
}
errors++;
validate59.errors = vErrors;
return false;
}
else {
errors = _errs0;
if(vErrors !== null){
if(_errs0){
vErrors.length = _errs0;
}
else {
vErrors = null;
}
}
}
validate59.errors = vErrors;
evaluated0.props = props1;
return errors === 0;
}
validate59.evaluated = {"dynamicProps":true,"dynamicItems":false};


function validate58(data, {instancePath="", parentData, parentDataProperty, rootData=data, dynamicAnchors={}}={}){
let vErrors = null;
let errors = 0;
const evaluated0 = validate58.evaluated;
if(evaluated0.dynamicProps){
evaluated0.props = undefined;
}
if(evaluated0.dynamicItems){
evaluated0.items = undefined;
}
const _errs0 = errors;
let valid0 = false;
let passing0 = null;
const _errs1 = errors;
if(errors === _errs1){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing0;
if((data.kind === undefined) && (missing0 = "kind")){
const err0 = {instancePath,schemaPath:"#/oneOf/0/required",keyword:"required",params:{missingProperty: missing0},message:"must have required property '"+missing0+"'"};
if(vErrors === null){
vErrors = [err0];
}
else {
vErrors.push(err0);
}
errors++;
}
else {
const _errs3 = errors;
for(const key0 in data){
if(!(key0 === "kind")){
const err1 = {instancePath,schemaPath:"#/oneOf/0/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key0},message:"must NOT have additional properties"};
if(vErrors === null){
vErrors = [err1];
}
else {
vErrors.push(err1);
}
errors++;
break;
}
}
if(_errs3 === errors){
if(data.kind !== undefined){
let data0 = data.kind;
if(typeof data0 !== "string"){
const err2 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/0/properties/kind/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err2];
}
else {
vErrors.push(err2);
}
errors++;
}
if("list" !== data0){
const err3 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/0/properties/kind/const",keyword:"const",params:{allowedValue: "list"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err3];
}
else {
vErrors.push(err3);
}
errors++;
}
}
}
}
}
else {
const err4 = {instancePath,schemaPath:"#/oneOf/0/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err4];
}
else {
vErrors.push(err4);
}
errors++;
}
}
var _valid0 = _errs1 === errors;
if(_valid0){
valid0 = true;
passing0 = 0;
var props0 = true;
}
const _errs6 = errors;
if(errors === _errs6){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing1;
if(((data.kind === undefined) && (missing1 = "kind")) || ((data.code === undefined) && (missing1 = "code"))){
const err5 = {instancePath,schemaPath:"#/oneOf/1/required",keyword:"required",params:{missingProperty: missing1},message:"must have required property '"+missing1+"'"};
if(vErrors === null){
vErrors = [err5];
}
else {
vErrors.push(err5);
}
errors++;
}
else {
const _errs8 = errors;
for(const key1 in data){
if(!((key1 === "code") || (key1 === "kind"))){
const err6 = {instancePath,schemaPath:"#/oneOf/1/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key1},message:"must NOT have additional properties"};
if(vErrors === null){
vErrors = [err6];
}
else {
vErrors.push(err6);
}
errors++;
break;
}
}
if(_errs8 === errors){
if(data.code !== undefined){
const _errs9 = errors;
if(typeof data.code !== "string"){
const err7 = {instancePath:instancePath+"/code",schemaPath:"#/oneOf/1/properties/code/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err7];
}
else {
vErrors.push(err7);
}
errors++;
}
var valid2 = _errs9 === errors;
}
else {
var valid2 = true;
}
if(valid2){
if(data.kind !== undefined){
let data2 = data.kind;
const _errs11 = errors;
if(typeof data2 !== "string"){
const err8 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/1/properties/kind/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err8];
}
else {
vErrors.push(err8);
}
errors++;
}
if("inspect" !== data2){
const err9 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/1/properties/kind/const",keyword:"const",params:{allowedValue: "inspect"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err9];
}
else {
vErrors.push(err9);
}
errors++;
}
var valid2 = _errs11 === errors;
}
else {
var valid2 = true;
}
}
}
}
}
else {
const err10 = {instancePath,schemaPath:"#/oneOf/1/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err10];
}
else {
vErrors.push(err10);
}
errors++;
}
}
var _valid0 = _errs6 === errors;
if(_valid0 && valid0){
valid0 = false;
passing0 = [passing0, 1];
}
else {
if(_valid0){
valid0 = true;
passing0 = 1;
if(props0 !== true){
props0 = true;
}
}
const _errs13 = errors;
if(errors === _errs13){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing2;
if((((((data.kind === undefined) && (missing2 = "kind")) || ((data.code === undefined) && (missing2 = "code"))) || ((data.nickname === undefined) && (missing2 = "nickname"))) || ((data.accepted_network === undefined) && (missing2 = "accepted_network"))) || ((data.operation_id === undefined) && (missing2 = "operation_id"))){
const err11 = {instancePath,schemaPath:"#/oneOf/2/required",keyword:"required",params:{missingProperty: missing2},message:"must have required property '"+missing2+"'"};
if(vErrors === null){
vErrors = [err11];
}
else {
vErrors.push(err11);
}
errors++;
}
else {
const _errs15 = errors;
for(const key2 in data){
if(!(((((key2 === "accepted_network") || (key2 === "code")) || (key2 === "kind")) || (key2 === "nickname")) || (key2 === "operation_id"))){
const err12 = {instancePath,schemaPath:"#/oneOf/2/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key2},message:"must NOT have additional properties"};
if(vErrors === null){
vErrors = [err12];
}
else {
vErrors.push(err12);
}
errors++;
break;
}
}
if(_errs15 === errors){
if(data.accepted_network !== undefined){
const _errs16 = errors;
if(typeof data.accepted_network !== "string"){
const err13 = {instancePath:instancePath+"/accepted_network",schemaPath:"#/oneOf/2/properties/accepted_network/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err13];
}
else {
vErrors.push(err13);
}
errors++;
}
var valid3 = _errs16 === errors;
}
else {
var valid3 = true;
}
if(valid3){
if(data.code !== undefined){
const _errs18 = errors;
if(typeof data.code !== "string"){
const err14 = {instancePath:instancePath+"/code",schemaPath:"#/oneOf/2/properties/code/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err14];
}
else {
vErrors.push(err14);
}
errors++;
}
var valid3 = _errs18 === errors;
}
else {
var valid3 = true;
}
if(valid3){
if(data.kind !== undefined){
let data5 = data.kind;
const _errs20 = errors;
if(typeof data5 !== "string"){
const err15 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/2/properties/kind/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err15];
}
else {
vErrors.push(err15);
}
errors++;
}
if("join" !== data5){
const err16 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/2/properties/kind/const",keyword:"const",params:{allowedValue: "join"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err16];
}
else {
vErrors.push(err16);
}
errors++;
}
var valid3 = _errs20 === errors;
}
else {
var valid3 = true;
}
if(valid3){
if(data.nickname !== undefined){
const _errs22 = errors;
if(typeof data.nickname !== "string"){
const err17 = {instancePath:instancePath+"/nickname",schemaPath:"#/oneOf/2/properties/nickname/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err17];
}
else {
vErrors.push(err17);
}
errors++;
}
var valid3 = _errs22 === errors;
}
else {
var valid3 = true;
}
if(valid3){
if(data.operation_id !== undefined){
const _errs24 = errors;
if(typeof data.operation_id !== "string"){
const err18 = {instancePath:instancePath+"/operation_id",schemaPath:"#/oneOf/2/properties/operation_id/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err18];
}
else {
vErrors.push(err18);
}
errors++;
}
var valid3 = _errs24 === errors;
}
else {
var valid3 = true;
}
}
}
}
}
}
}
}
else {
const err19 = {instancePath,schemaPath:"#/oneOf/2/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err19];
}
else {
vErrors.push(err19);
}
errors++;
}
}
var _valid0 = _errs13 === errors;
if(_valid0 && valid0){
valid0 = false;
passing0 = [passing0, 2];
}
else {
if(_valid0){
valid0 = true;
passing0 = 2;
if(props0 !== true){
props0 = true;
}
}
const _errs26 = errors;
if(errors === _errs26){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing3;
if((((data.kind === undefined) && (missing3 = "kind")) || ((data.network === undefined) && (missing3 = "network"))) || ((data.request === undefined) && (missing3 = "request"))){
const err20 = {instancePath,schemaPath:"#/oneOf/3/required",keyword:"required",params:{missingProperty: missing3},message:"must have required property '"+missing3+"'"};
if(vErrors === null){
vErrors = [err20];
}
else {
vErrors.push(err20);
}
errors++;
}
else {
const _errs28 = errors;
for(const key3 in data){
if(!(((key3 === "kind") || (key3 === "network")) || (key3 === "request"))){
const err21 = {instancePath,schemaPath:"#/oneOf/3/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key3},message:"must NOT have additional properties"};
if(vErrors === null){
vErrors = [err21];
}
else {
vErrors.push(err21);
}
errors++;
break;
}
}
if(_errs28 === errors){
if(data.kind !== undefined){
let data8 = data.kind;
const _errs29 = errors;
if(typeof data8 !== "string"){
const err22 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/3/properties/kind/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err22];
}
else {
vErrors.push(err22);
}
errors++;
}
if("call" !== data8){
const err23 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/3/properties/kind/const",keyword:"const",params:{allowedValue: "call"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err23];
}
else {
vErrors.push(err23);
}
errors++;
}
var valid4 = _errs29 === errors;
}
else {
var valid4 = true;
}
if(valid4){
if(data.network !== undefined){
const _errs31 = errors;
if(typeof data.network !== "string"){
const err24 = {instancePath:instancePath+"/network",schemaPath:"#/oneOf/3/properties/network/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err24];
}
else {
vErrors.push(err24);
}
errors++;
}
var valid4 = _errs31 === errors;
}
else {
var valid4 = true;
}
if(valid4){
if(data.request !== undefined){
const _errs33 = errors;
if(!(validate59(data.request, {instancePath:instancePath+"/request",parentData:data,parentDataProperty:"request",rootData,dynamicAnchors}))){
vErrors = vErrors === null ? validate59.errors : vErrors.concat(validate59.errors);
errors = vErrors.length;
}
var valid4 = _errs33 === errors;
}
else {
var valid4 = true;
}
}
}
}
}
}
else {
const err25 = {instancePath,schemaPath:"#/oneOf/3/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err25];
}
else {
vErrors.push(err25);
}
errors++;
}
}
var _valid0 = _errs26 === errors;
if(_valid0 && valid0){
valid0 = false;
passing0 = [passing0, 3];
}
else {
if(_valid0){
valid0 = true;
passing0 = 3;
if(props0 !== true){
props0 = true;
}
}
}
}
}
if(!valid0){
const err26 = {instancePath,schemaPath:"#/oneOf",keyword:"oneOf",params:{passingSchemas: passing0},message:"must match exactly one schema in oneOf"};
if(vErrors === null){
vErrors = [err26];
}
else {
vErrors.push(err26);
}
errors++;
validate58.errors = vErrors;
return false;
}
else {
errors = _errs0;
if(vErrors !== null){
if(_errs0){
vErrors.length = _errs0;
}
else {
vErrors = null;
}
}
}
validate58.errors = vErrors;
evaluated0.props = props0;
return errors === 0;
}
validate58.evaluated = {"dynamicProps":true,"dynamicItems":false};


function validate57(data, {instancePath="", parentData, parentDataProperty, rootData=data, dynamicAnchors={}}={}){
let vErrors = null;
let errors = 0;
const evaluated0 = validate57.evaluated;
if(evaluated0.dynamicProps){
evaluated0.props = undefined;
}
if(evaluated0.dynamicItems){
evaluated0.items = undefined;
}
if(errors === 0){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing0;
if((data.request === undefined) && (missing0 = "request")){
validate57.errors = [{instancePath,schemaPath:"#/required",keyword:"required",params:{missingProperty: missing0},message:"must have required property '"+missing0+"'"}];
return false;
}
else {
const _errs1 = errors;
for(const key0 in data){
if(!(key0 === "request")){
validate57.errors = [{instancePath,schemaPath:"#/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key0},message:"must NOT have additional properties"}];
return false;
break;
}
}
if(_errs1 === errors){
if(data.request !== undefined){
if(!(validate58(data.request, {instancePath:instancePath+"/request",parentData:data,parentDataProperty:"request",rootData,dynamicAnchors}))){
vErrors = vErrors === null ? validate58.errors : vErrors.concat(validate58.errors);
errors = vErrors.length;
}
}
}
}
}
else {
validate57.errors = [{instancePath,schemaPath:"#/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
validate57.errors = vErrors;
return errors === 0;
}
validate57.evaluated = {"props":true,"dynamicProps":false,"dynamicItems":false};

export const networks_output = validate62;
const schema70 = {"$defs":{"ActionResult":{"properties":{"artifacts":{"items":{"$ref":"#/$defs/Artifact"},"type":"array"},"details":{"items":{"type":"string"},"type":"array"},"id":{"type":"string"},"messageId":{"default":null,"type":["string","null"]},"outputBase64":{"description":"Exact signed bytes, base64 encoded; views decode only for display.","type":["string","null"]},"state":{"type":"string"},"stderr":{"type":"boolean"}},"required":["id","state","stderr","details","artifacts"],"type":"object"},"Activity":{"description":"Authenticated state changes observed by this profile, retained before publication.","properties":{"conversation":{"type":"string"},"id":{"type":"string"},"kind":{"type":"string"},"text":{"type":"string"},"timestamp":{"format":"uint64","minimum":0,"type":"integer"}},"required":["id","conversation","kind","text","timestamp"],"type":"object"},"Artifact":{"properties":{"name":{"type":"string"},"url":{"type":"string"}},"required":["name","url"],"type":"object"},"CommandOutput":{"oneOf":[{"properties":{"commands":{"items":{"$ref":"#/$defs/CommandSpec"},"type":"array"},"kind":{"const":"help","type":"string"}},"required":["kind","commands"],"type":"object"},{"properties":{"channels":{"items":{"$ref":"#/$defs/DirectoryEntry"},"type":"array"},"kind":{"const":"directory","type":"string"}},"required":["kind","channels"],"type":"object"},{"properties":{"channel":{"type":"string"},"expires":{"format":"uint64","minimum":0,"type":"integer"},"kind":{"const":"invitation","type":"string"},"link":{"type":"string"},"localOnly":{"default":false,"type":"boolean"}},"required":["kind","channel","link","expires"],"type":"object"},{"properties":{"kind":{"const":"text","type":"string"},"text":{"type":"string"},"title":{"type":"string"}},"required":["kind","title","text"],"type":"object"},{"properties":{"kind":{"const":"status","type":"string"},"text":{"type":"string"}},"required":["kind","text"],"type":"object"},{"properties":{"conversation":{"type":"string"},"kind":{"const":"close","type":"string"}},"required":["kind","conversation"],"type":"object"}]},"CommandSpec":{"properties":{"available":{"type":"boolean"},"capability":{"type":["string","null"]},"description":{"type":"string"},"name":{"type":"string"},"scope":{"type":"string"},"usage":{"type":"string"}},"required":["name","usage","description","scope","available"],"type":"object"},"Completion":{"properties":{"description":{"type":"string"},"text":{"type":"string"}},"required":["text","description"],"type":"object"},"Conversation":{"properties":{"active":{"type":"boolean"},"channelId":{"type":"string"},"commands":{"default":[],"items":{"$ref":"#/$defs/CommandSpec"},"type":"array"},"directory":{"default":null,"type":["string","null"]},"id":{"type":"string"},"inputLimitBytes":{"default":12000,"format":"uint","minimum":0,"type":"integer"},"kind":{"$ref":"#/$defs/ConversationKind"},"lastMessageId":{"type":["string","null"]},"members":{"items":{"$ref":"#/$defs/Member"},"type":"array"},"name":{"type":"string"},"owner":{"type":"boolean"},"provider":{"default":null,"type":["string","null"]},"topic":{"type":"string"},"unread":{"format":"uint32","minimum":0,"type":"integer"},"visibility":{"default":null,"type":["string","null"]}},"required":["id","channelId","kind","name","topic","active","owner","members","unread"],"type":"object"},"ConversationKind":{"enum":["channel","query","archive"],"type":"string"},"Delivery":{"enum":["local_accepted","delivered"],"type":"string"},"DirectoryEntry":{"properties":{"conversation":{"type":["string","null"]},"joined":{"type":"boolean"},"name":{"type":"string"}},"required":["name","joined"],"type":"object"},"FileInfo":{"additionalProperties":false,"properties":{"aliases":{"default":null,"items":{"type":"string"},"type":["array","null"]},"completed_by":{"format":"uint16","maximum":65535,"minimum":0,"type":"integer"},"conversation":{"type":"string"},"error":{"type":["string","null"]},"id":{"type":"string"},"name":{"type":"string"},"size_bytes":{"type":"string"},"sources":{"format":"uint16","maximum":65535,"minimum":0,"type":"integer"},"state":{"$ref":"#/$defs/FileState"},"verified_bytes":{"type":"string"},"verified_sources":{"default":0,"description":"Peers contributing verified pieces since this process opened the cache.","format":"uint16","maximum":65535,"minimum":0,"type":"integer"}},"required":["id","conversation","name","size_bytes","verified_bytes","state","sources","completed_by"],"type":"object"},"FileSnapshot":{"additionalProperties":false,"properties":{"files":{"items":{"$ref":"#/$defs/FileInfo"},"type":"array"},"quota_bytes":{"type":"string"},"retention_days":{"format":"uint16","maximum":65535,"minimum":0,"type":"integer"},"used_bytes":{"type":"string"}},"required":["files","quota_bytes","used_bytes","retention_days"],"type":"object"},"FileState":{"enum":["offered","importing","downloading","waiting_for_peers","paused","complete","failed","cancelled"],"type":"string"},"HistoryPage":{"properties":{"before":{"type":["string","null"]},"messages":{"items":{"$ref":"#/$defs/Message"},"type":"array"}},"required":["messages"],"type":"object"},"InputHistoryEntry":{"properties":{"conversation":{"type":["string","null"]},"text":{"type":"string"}},"required":["text"],"type":"object"},"InstanceInfo":{"properties":{"archiveExists":{"type":"boolean"},"bootId":{"type":"string"},"capabilities":{"items":{"type":"string"},"type":"array"},"id":{"type":"string"},"label":{"type":"string"},"locked":{"type":"boolean"},"profileExists":{"type":"boolean"},"protocolLocked":{"type":"boolean"},"safetyNumber":{"type":"string"}},"required":["id","label","bootId","locked","protocolLocked","profileExists","archiveExists","safetyNumber","capabilities"],"type":"object"},"InvitationPreview":{"properties":{"channel":{"type":["string","null"]},"expires":{"format":"uint64","minimum":0,"type":"integer"},"network":{"$ref":"#/$defs/JoinedNetwork"},"newNetwork":{"type":"boolean"}},"required":["network","newNetwork","expires"],"type":"object"},"JoinedNetwork":{"properties":{"fingerprint":{"type":"string"},"id":{"type":"string"},"name":{"type":"string"},"primary":{"type":"boolean"},"status":{"$ref":"#/$defs/NetworkStatus"}},"required":["id","name","fingerprint","primary","status"],"type":"object"},"Member":{"properties":{"capabilities":{"default":[],"items":{"type":"string"},"type":"array"},"id":{"type":"string"},"isSelf":{"type":"boolean"},"nickname":{"type":"string"},"recentlyActive":{"default":null,"type":["boolean","null"]}},"required":["id","nickname","isSelf"],"type":"object"},"Message":{"properties":{"body":{"type":"string"},"conversationId":{"type":"string"},"delivery":{"anyOf":[{"$ref":"#/$defs/Delivery"},{"type":"null"}],"description":"Delivered is an authenticated recipient acknowledgement, never a read receipt."},"id":{"type":"string"},"memberId":{"type":["string","null"]},"mine":{"type":"boolean"},"nickname":{"type":"string"},"operationId":{"default":null,"type":["string","null"]},"result":{"anyOf":[{"$ref":"#/$defs/ActionResult"},{"type":"null"}],"default":null},"timestamp":{"format":"uint64","minimum":0,"type":"integer"}},"required":["id","conversationId","nickname","body","timestamp","mine"],"type":"object"},"NetworkState":{"description":"Public connection progress; never contains invitations or private routing cards.","enum":["locked","local_only","invitation_required","connecting","connected","reconnecting","invitation_expired","unavailable"],"type":"string"},"NetworkStatus":{"properties":{"message":{"type":"string"},"state":{"$ref":"#/$defs/NetworkState"}},"required":["state","message"],"type":"object"},"OperationDetail":{"description":"Safe metadata plus the protected result retained in the encrypted operation journal.","properties":{"action":{"type":"string"},"conversation":{"type":["string","null"]},"id":{"type":"string"},"instance":{"type":"string"},"message":{"type":["string","null"]},"network":{"default":null,"type":["string","null"]},"output":{"anyOf":[{"$ref":"#/$defs/CommandOutput"},{"type":"null"}]},"started":{"format":"uint64","minimum":0,"type":"integer"},"state":{"type":"string"}},"required":["id","instance","action","started","state"],"type":"object"},"ProviderStatus":{"properties":{"code":{"type":"string"},"id":{"type":"string"},"message":{"type":"string"},"retryable":{"type":"boolean"}},"required":["id","code","message","retryable"],"type":"object"},"Response":{"oneOf":[{"properties":{"kind":{"const":"networks","type":"string"},"response":{"$ref":"#"}},"required":["kind","response"],"type":"object"},{"properties":{"kind":{"const":"files","type":"string"},"snapshot":{"$ref":"#/$defs/FileSnapshot"}},"required":["kind","snapshot"],"type":"object"},{"properties":{"kind":{"const":"network_status","type":"string"},"status":{"$ref":"#/$defs/NetworkStatus"}},"required":["kind","status"],"type":"object"},{"properties":{"instance":{"$ref":"#/$defs/InstanceInfo"},"kind":{"const":"instance","type":"string"}},"required":["kind","instance"],"type":"object"},{"properties":{"kind":{"const":"snapshot","type":"string"},"snapshot":{"$ref":"#/$defs/Snapshot"}},"required":["kind","snapshot"],"type":"object"},{"properties":{"kind":{"const":"history","type":"string"},"page":{"$ref":"#/$defs/HistoryPage"}},"required":["kind","page"],"type":"object"},{"properties":{"items":{"items":{"$ref":"#/$defs/Completion"},"type":"array"},"kind":{"const":"completed","type":"string"}},"required":["kind","items"],"type":"object"},{"properties":{"commands":{"items":{"$ref":"#/$defs/CommandSpec"},"type":"array"},"kind":{"const":"catalogue","type":"string"}},"required":["kind","commands"],"type":"object"},{"properties":{"conversations":{"items":{"$ref":"#/$defs/Conversation"},"type":"array"},"kind":{"const":"projection","type":"string"},"revision":{"type":"string"}},"required":["kind","conversations","revision"],"type":"object"},{"properties":{"conversation":{"type":["string","null"]},"kind":{"const":"output","type":"string"},"output":{"$ref":"#/$defs/CommandOutput"}},"required":["kind","output"],"type":"object"},{"properties":{"conversation":{"type":["string","null"]},"kind":{"const":"applied","type":"string"},"notice":{"type":["string","null"]}},"required":["kind"],"type":"object"},{"properties":{"kind":{"const":"changed","type":"string"},"revision":{"type":"string"}},"required":["kind","revision"],"type":"object"},{"properties":{"code":{"type":"string"},"kind":{"const":"error","type":"string"},"message":{"type":"string"}},"required":["kind","code","message"],"type":"object"}]},"Snapshot":{"properties":{"activity":{"default":null,"items":{"$ref":"#/$defs/Activity"},"type":["array","null"]},"commandHistory":{"items":{"type":"string"},"type":"array"},"conversations":{"items":{"$ref":"#/$defs/Conversation"},"type":"array"},"inputHistory":{"items":{"$ref":"#/$defs/InputHistoryEntry"},"type":"array"},"instance":{"$ref":"#/$defs/InstanceInfo"},"operations":{"default":null,"items":{"$ref":"#/$defs/OperationDetail"},"type":["array","null"]},"presenceEnabled":{"default":null,"type":["boolean","null"]},"providerErrors":{"default":[],"items":{"$ref":"#/$defs/ProviderStatus"},"type":"array"},"revision":{"type":"string"}},"required":["instance","revision","conversations","commandHistory","inputHistory"],"type":"object"}},"$schema":"https://json-schema.org/draft/2020-12/schema","oneOf":[{"properties":{"kind":{"const":"list","type":"string"},"networks":{"items":{"$ref":"#/$defs/JoinedNetwork"},"type":"array"}},"required":["kind","networks"],"type":"object"},{"properties":{"kind":{"const":"preview","type":"string"},"preview":{"$ref":"#/$defs/InvitationPreview"}},"required":["kind","preview"],"type":"object"},{"properties":{"kind":{"const":"result","type":"string"},"network":{"type":"string"},"response":{"$ref":"#/$defs/Response"}},"required":["kind","network","response"],"type":"object"}],"title":"NetworkResponse"};
const schema71 = {"properties":{"fingerprint":{"type":"string"},"id":{"type":"string"},"name":{"type":"string"},"primary":{"type":"boolean"},"status":{"$ref":"#/$defs/NetworkStatus"}},"required":["id","name","fingerprint","primary","status"],"type":"object"};
const schema72 = {"properties":{"message":{"type":"string"},"state":{"$ref":"#/$defs/NetworkState"}},"required":["state","message"],"type":"object"};
const schema73 = {"description":"Public connection progress; never contains invitations or private routing cards.","enum":["locked","local_only","invitation_required","connecting","connected","reconnecting","invitation_expired","unavailable"],"type":"string"};

function validate64(data, {instancePath="", parentData, parentDataProperty, rootData=data, dynamicAnchors={}}={}){
let vErrors = null;
let errors = 0;
const evaluated0 = validate64.evaluated;
if(evaluated0.dynamicProps){
evaluated0.props = undefined;
}
if(evaluated0.dynamicItems){
evaluated0.items = undefined;
}
if(errors === 0){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing0;
if(((data.state === undefined) && (missing0 = "state")) || ((data.message === undefined) && (missing0 = "message"))){
validate64.errors = [{instancePath,schemaPath:"#/required",keyword:"required",params:{missingProperty: missing0},message:"must have required property '"+missing0+"'"}];
return false;
}
else {
if(data.message !== undefined){
const _errs1 = errors;
if(typeof data.message !== "string"){
validate64.errors = [{instancePath:instancePath+"/message",schemaPath:"#/properties/message/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs1 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.state !== undefined){
let data1 = data.state;
const _errs3 = errors;
if(typeof data1 !== "string"){
validate64.errors = [{instancePath:instancePath+"/state",schemaPath:"#/$defs/NetworkState/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
if(!((((((((data1 === "locked") || (data1 === "local_only")) || (data1 === "invitation_required")) || (data1 === "connecting")) || (data1 === "connected")) || (data1 === "reconnecting")) || (data1 === "invitation_expired")) || (data1 === "unavailable"))){
validate64.errors = [{instancePath:instancePath+"/state",schemaPath:"#/$defs/NetworkState/enum",keyword:"enum",params:{allowedValues: schema73.enum},message:"must be equal to one of the allowed values"}];
return false;
}
var valid0 = _errs3 === errors;
}
else {
var valid0 = true;
}
}
}
}
else {
validate64.errors = [{instancePath,schemaPath:"#/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
validate64.errors = vErrors;
return errors === 0;
}
validate64.evaluated = {"props":{"message":true,"state":true},"dynamicProps":false,"dynamicItems":false};


function validate63(data, {instancePath="", parentData, parentDataProperty, rootData=data, dynamicAnchors={}}={}){
let vErrors = null;
let errors = 0;
const evaluated0 = validate63.evaluated;
if(evaluated0.dynamicProps){
evaluated0.props = undefined;
}
if(evaluated0.dynamicItems){
evaluated0.items = undefined;
}
if(errors === 0){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing0;
if((((((data.id === undefined) && (missing0 = "id")) || ((data.name === undefined) && (missing0 = "name"))) || ((data.fingerprint === undefined) && (missing0 = "fingerprint"))) || ((data.primary === undefined) && (missing0 = "primary"))) || ((data.status === undefined) && (missing0 = "status"))){
validate63.errors = [{instancePath,schemaPath:"#/required",keyword:"required",params:{missingProperty: missing0},message:"must have required property '"+missing0+"'"}];
return false;
}
else {
if(data.fingerprint !== undefined){
const _errs1 = errors;
if(typeof data.fingerprint !== "string"){
validate63.errors = [{instancePath:instancePath+"/fingerprint",schemaPath:"#/properties/fingerprint/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs1 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.id !== undefined){
const _errs3 = errors;
if(typeof data.id !== "string"){
validate63.errors = [{instancePath:instancePath+"/id",schemaPath:"#/properties/id/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs3 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.name !== undefined){
const _errs5 = errors;
if(typeof data.name !== "string"){
validate63.errors = [{instancePath:instancePath+"/name",schemaPath:"#/properties/name/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs5 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.primary !== undefined){
const _errs7 = errors;
if(typeof data.primary !== "boolean"){
validate63.errors = [{instancePath:instancePath+"/primary",schemaPath:"#/properties/primary/type",keyword:"type",params:{type: "boolean"},message:"must be boolean"}];
return false;
}
var valid0 = _errs7 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.status !== undefined){
const _errs9 = errors;
if(!(validate64(data.status, {instancePath:instancePath+"/status",parentData:data,parentDataProperty:"status",rootData,dynamicAnchors}))){
vErrors = vErrors === null ? validate64.errors : vErrors.concat(validate64.errors);
errors = vErrors.length;
}
var valid0 = _errs9 === errors;
}
else {
var valid0 = true;
}
}
}
}
}
}
}
else {
validate63.errors = [{instancePath,schemaPath:"#/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
validate63.errors = vErrors;
return errors === 0;
}
validate63.evaluated = {"props":{"fingerprint":true,"id":true,"name":true,"primary":true,"status":true},"dynamicProps":false,"dynamicItems":false};

const schema74 = {"properties":{"channel":{"type":["string","null"]},"expires":{"format":"uint64","minimum":0,"type":"integer"},"network":{"$ref":"#/$defs/JoinedNetwork"},"newNetwork":{"type":"boolean"}},"required":["network","newNetwork","expires"],"type":"object"};

function validate67(data, {instancePath="", parentData, parentDataProperty, rootData=data, dynamicAnchors={}}={}){
let vErrors = null;
let errors = 0;
const evaluated0 = validate67.evaluated;
if(evaluated0.dynamicProps){
evaluated0.props = undefined;
}
if(evaluated0.dynamicItems){
evaluated0.items = undefined;
}
if(errors === 0){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing0;
if((((data.network === undefined) && (missing0 = "network")) || ((data.newNetwork === undefined) && (missing0 = "newNetwork"))) || ((data.expires === undefined) && (missing0 = "expires"))){
validate67.errors = [{instancePath,schemaPath:"#/required",keyword:"required",params:{missingProperty: missing0},message:"must have required property '"+missing0+"'"}];
return false;
}
else {
if(data.channel !== undefined){
let data0 = data.channel;
const _errs1 = errors;
if((typeof data0 !== "string") && (data0 !== null)){
validate67.errors = [{instancePath:instancePath+"/channel",schemaPath:"#/properties/channel/type",keyword:"type",params:{type: schema74.properties.channel.type},message:"must be string,null"}];
return false;
}
var valid0 = _errs1 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.expires !== undefined){
let data1 = data.expires;
const _errs3 = errors;
if(!(((typeof data1 == "number") && (!(data1 % 1) && !isNaN(data1))) && (isFinite(data1)))){
validate67.errors = [{instancePath:instancePath+"/expires",schemaPath:"#/properties/expires/type",keyword:"type",params:{type: "integer"},message:"must be integer"}];
return false;
}
if(errors === _errs3){
if((typeof data1 == "number") && (isFinite(data1))){
if(data1 < 0 || isNaN(data1)){
validate67.errors = [{instancePath:instancePath+"/expires",schemaPath:"#/properties/expires/minimum",keyword:"minimum",params:{comparison: ">=", limit: 0},message:"must be >= 0"}];
return false;
}
}
}
var valid0 = _errs3 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.network !== undefined){
const _errs5 = errors;
if(!(validate63(data.network, {instancePath:instancePath+"/network",parentData:data,parentDataProperty:"network",rootData,dynamicAnchors}))){
vErrors = vErrors === null ? validate63.errors : vErrors.concat(validate63.errors);
errors = vErrors.length;
}
var valid0 = _errs5 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.newNetwork !== undefined){
const _errs6 = errors;
if(typeof data.newNetwork !== "boolean"){
validate67.errors = [{instancePath:instancePath+"/newNetwork",schemaPath:"#/properties/newNetwork/type",keyword:"type",params:{type: "boolean"},message:"must be boolean"}];
return false;
}
var valid0 = _errs6 === errors;
}
else {
var valid0 = true;
}
}
}
}
}
}
else {
validate67.errors = [{instancePath,schemaPath:"#/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
validate67.errors = vErrors;
return errors === 0;
}
validate67.evaluated = {"props":{"channel":true,"expires":true,"network":true,"newNetwork":true},"dynamicProps":false,"dynamicItems":false};

const schema75 = {"oneOf":[{"properties":{"kind":{"const":"networks","type":"string"},"response":{"$ref":"#"}},"required":["kind","response"],"type":"object"},{"properties":{"kind":{"const":"files","type":"string"},"snapshot":{"$ref":"#/$defs/FileSnapshot"}},"required":["kind","snapshot"],"type":"object"},{"properties":{"kind":{"const":"network_status","type":"string"},"status":{"$ref":"#/$defs/NetworkStatus"}},"required":["kind","status"],"type":"object"},{"properties":{"instance":{"$ref":"#/$defs/InstanceInfo"},"kind":{"const":"instance","type":"string"}},"required":["kind","instance"],"type":"object"},{"properties":{"kind":{"const":"snapshot","type":"string"},"snapshot":{"$ref":"#/$defs/Snapshot"}},"required":["kind","snapshot"],"type":"object"},{"properties":{"kind":{"const":"history","type":"string"},"page":{"$ref":"#/$defs/HistoryPage"}},"required":["kind","page"],"type":"object"},{"properties":{"items":{"items":{"$ref":"#/$defs/Completion"},"type":"array"},"kind":{"const":"completed","type":"string"}},"required":["kind","items"],"type":"object"},{"properties":{"commands":{"items":{"$ref":"#/$defs/CommandSpec"},"type":"array"},"kind":{"const":"catalogue","type":"string"}},"required":["kind","commands"],"type":"object"},{"properties":{"conversations":{"items":{"$ref":"#/$defs/Conversation"},"type":"array"},"kind":{"const":"projection","type":"string"},"revision":{"type":"string"}},"required":["kind","conversations","revision"],"type":"object"},{"properties":{"conversation":{"type":["string","null"]},"kind":{"const":"output","type":"string"},"output":{"$ref":"#/$defs/CommandOutput"}},"required":["kind","output"],"type":"object"},{"properties":{"conversation":{"type":["string","null"]},"kind":{"const":"applied","type":"string"},"notice":{"type":["string","null"]}},"required":["kind"],"type":"object"},{"properties":{"kind":{"const":"changed","type":"string"},"revision":{"type":"string"}},"required":["kind","revision"],"type":"object"},{"properties":{"code":{"type":"string"},"kind":{"const":"error","type":"string"},"message":{"type":"string"}},"required":["kind","code","message"],"type":"object"}]};
const schema79 = {"properties":{"archiveExists":{"type":"boolean"},"bootId":{"type":"string"},"capabilities":{"items":{"type":"string"},"type":"array"},"id":{"type":"string"},"label":{"type":"string"},"locked":{"type":"boolean"},"profileExists":{"type":"boolean"},"protocolLocked":{"type":"boolean"},"safetyNumber":{"type":"string"}},"required":["id","label","bootId","locked","protocolLocked","profileExists","archiveExists","safetyNumber","capabilities"],"type":"object"};
const schema98 = {"properties":{"description":{"type":"string"},"text":{"type":"string"}},"required":["text","description"],"type":"object"};
const schema83 = {"properties":{"available":{"type":"boolean"},"capability":{"type":["string","null"]},"description":{"type":"string"},"name":{"type":"string"},"scope":{"type":"string"},"usage":{"type":"string"}},"required":["name","usage","description","scope","available"],"type":"object"};
const root1 = {validate: validate62};
const schema76 = {"additionalProperties":false,"properties":{"files":{"items":{"$ref":"#/$defs/FileInfo"},"type":"array"},"quota_bytes":{"type":"string"},"retention_days":{"format":"uint16","maximum":65535,"minimum":0,"type":"integer"},"used_bytes":{"type":"string"}},"required":["files","quota_bytes","used_bytes","retention_days"],"type":"object"};
const schema77 = {"additionalProperties":false,"properties":{"aliases":{"default":null,"items":{"type":"string"},"type":["array","null"]},"completed_by":{"format":"uint16","maximum":65535,"minimum":0,"type":"integer"},"conversation":{"type":"string"},"error":{"type":["string","null"]},"id":{"type":"string"},"name":{"type":"string"},"size_bytes":{"type":"string"},"sources":{"format":"uint16","maximum":65535,"minimum":0,"type":"integer"},"state":{"$ref":"#/$defs/FileState"},"verified_bytes":{"type":"string"},"verified_sources":{"default":0,"description":"Peers contributing verified pieces since this process opened the cache.","format":"uint16","maximum":65535,"minimum":0,"type":"integer"}},"required":["id","conversation","name","size_bytes","verified_bytes","state","sources","completed_by"],"type":"object"};
const schema78 = {"enum":["offered","importing","downloading","waiting_for_peers","paused","complete","failed","cancelled"],"type":"string"};

function validate72(data, {instancePath="", parentData, parentDataProperty, rootData=data, dynamicAnchors={}}={}){
let vErrors = null;
let errors = 0;
const evaluated0 = validate72.evaluated;
if(evaluated0.dynamicProps){
evaluated0.props = undefined;
}
if(evaluated0.dynamicItems){
evaluated0.items = undefined;
}
if(errors === 0){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing0;
if(((((((((data.id === undefined) && (missing0 = "id")) || ((data.conversation === undefined) && (missing0 = "conversation"))) || ((data.name === undefined) && (missing0 = "name"))) || ((data.size_bytes === undefined) && (missing0 = "size_bytes"))) || ((data.verified_bytes === undefined) && (missing0 = "verified_bytes"))) || ((data.state === undefined) && (missing0 = "state"))) || ((data.sources === undefined) && (missing0 = "sources"))) || ((data.completed_by === undefined) && (missing0 = "completed_by"))){
validate72.errors = [{instancePath,schemaPath:"#/required",keyword:"required",params:{missingProperty: missing0},message:"must have required property '"+missing0+"'"}];
return false;
}
else {
const _errs1 = errors;
for(const key0 in data){
if(!(func1.call(schema77.properties, key0))){
validate72.errors = [{instancePath,schemaPath:"#/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key0},message:"must NOT have additional properties"}];
return false;
break;
}
}
if(_errs1 === errors){
if(data.aliases !== undefined){
let data0 = data.aliases;
const _errs2 = errors;
if((!(Array.isArray(data0))) && (data0 !== null)){
validate72.errors = [{instancePath:instancePath+"/aliases",schemaPath:"#/properties/aliases/type",keyword:"type",params:{type: schema77.properties.aliases.type},message:"must be array,null"}];
return false;
}
if(errors === _errs2){
if(Array.isArray(data0)){
var valid1 = true;
const len0 = data0.length;
for(let i0=0; i0<len0; i0++){
const _errs4 = errors;
if(typeof data0[i0] !== "string"){
validate72.errors = [{instancePath:instancePath+"/aliases/" + i0,schemaPath:"#/properties/aliases/items/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid1 = _errs4 === errors;
if(!valid1){
break;
}
}
}
}
var valid0 = _errs2 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.completed_by !== undefined){
let data2 = data.completed_by;
const _errs6 = errors;
if(!(((typeof data2 == "number") && (!(data2 % 1) && !isNaN(data2))) && (isFinite(data2)))){
validate72.errors = [{instancePath:instancePath+"/completed_by",schemaPath:"#/properties/completed_by/type",keyword:"type",params:{type: "integer"},message:"must be integer"}];
return false;
}
if(errors === _errs6){
if((typeof data2 == "number") && (isFinite(data2))){
if(data2 > 65535 || isNaN(data2)){
validate72.errors = [{instancePath:instancePath+"/completed_by",schemaPath:"#/properties/completed_by/maximum",keyword:"maximum",params:{comparison: "<=", limit: 65535},message:"must be <= 65535"}];
return false;
}
else {
if(data2 < 0 || isNaN(data2)){
validate72.errors = [{instancePath:instancePath+"/completed_by",schemaPath:"#/properties/completed_by/minimum",keyword:"minimum",params:{comparison: ">=", limit: 0},message:"must be >= 0"}];
return false;
}
}
}
}
var valid0 = _errs6 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.conversation !== undefined){
const _errs8 = errors;
if(typeof data.conversation !== "string"){
validate72.errors = [{instancePath:instancePath+"/conversation",schemaPath:"#/properties/conversation/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs8 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.error !== undefined){
let data4 = data.error;
const _errs10 = errors;
if((typeof data4 !== "string") && (data4 !== null)){
validate72.errors = [{instancePath:instancePath+"/error",schemaPath:"#/properties/error/type",keyword:"type",params:{type: schema77.properties.error.type},message:"must be string,null"}];
return false;
}
var valid0 = _errs10 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.id !== undefined){
const _errs12 = errors;
if(typeof data.id !== "string"){
validate72.errors = [{instancePath:instancePath+"/id",schemaPath:"#/properties/id/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs12 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.name !== undefined){
const _errs14 = errors;
if(typeof data.name !== "string"){
validate72.errors = [{instancePath:instancePath+"/name",schemaPath:"#/properties/name/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs14 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.size_bytes !== undefined){
const _errs16 = errors;
if(typeof data.size_bytes !== "string"){
validate72.errors = [{instancePath:instancePath+"/size_bytes",schemaPath:"#/properties/size_bytes/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs16 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.sources !== undefined){
let data8 = data.sources;
const _errs18 = errors;
if(!(((typeof data8 == "number") && (!(data8 % 1) && !isNaN(data8))) && (isFinite(data8)))){
validate72.errors = [{instancePath:instancePath+"/sources",schemaPath:"#/properties/sources/type",keyword:"type",params:{type: "integer"},message:"must be integer"}];
return false;
}
if(errors === _errs18){
if((typeof data8 == "number") && (isFinite(data8))){
if(data8 > 65535 || isNaN(data8)){
validate72.errors = [{instancePath:instancePath+"/sources",schemaPath:"#/properties/sources/maximum",keyword:"maximum",params:{comparison: "<=", limit: 65535},message:"must be <= 65535"}];
return false;
}
else {
if(data8 < 0 || isNaN(data8)){
validate72.errors = [{instancePath:instancePath+"/sources",schemaPath:"#/properties/sources/minimum",keyword:"minimum",params:{comparison: ">=", limit: 0},message:"must be >= 0"}];
return false;
}
}
}
}
var valid0 = _errs18 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.state !== undefined){
let data9 = data.state;
const _errs20 = errors;
if(typeof data9 !== "string"){
validate72.errors = [{instancePath:instancePath+"/state",schemaPath:"#/$defs/FileState/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
if(!((((((((data9 === "offered") || (data9 === "importing")) || (data9 === "downloading")) || (data9 === "waiting_for_peers")) || (data9 === "paused")) || (data9 === "complete")) || (data9 === "failed")) || (data9 === "cancelled"))){
validate72.errors = [{instancePath:instancePath+"/state",schemaPath:"#/$defs/FileState/enum",keyword:"enum",params:{allowedValues: schema78.enum},message:"must be equal to one of the allowed values"}];
return false;
}
var valid0 = _errs20 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.verified_bytes !== undefined){
const _errs23 = errors;
if(typeof data.verified_bytes !== "string"){
validate72.errors = [{instancePath:instancePath+"/verified_bytes",schemaPath:"#/properties/verified_bytes/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs23 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.verified_sources !== undefined){
let data11 = data.verified_sources;
const _errs25 = errors;
if(!(((typeof data11 == "number") && (!(data11 % 1) && !isNaN(data11))) && (isFinite(data11)))){
validate72.errors = [{instancePath:instancePath+"/verified_sources",schemaPath:"#/properties/verified_sources/type",keyword:"type",params:{type: "integer"},message:"must be integer"}];
return false;
}
if(errors === _errs25){
if((typeof data11 == "number") && (isFinite(data11))){
if(data11 > 65535 || isNaN(data11)){
validate72.errors = [{instancePath:instancePath+"/verified_sources",schemaPath:"#/properties/verified_sources/maximum",keyword:"maximum",params:{comparison: "<=", limit: 65535},message:"must be <= 65535"}];
return false;
}
else {
if(data11 < 0 || isNaN(data11)){
validate72.errors = [{instancePath:instancePath+"/verified_sources",schemaPath:"#/properties/verified_sources/minimum",keyword:"minimum",params:{comparison: ">=", limit: 0},message:"must be >= 0"}];
return false;
}
}
}
}
var valid0 = _errs25 === errors;
}
else {
var valid0 = true;
}
}
}
}
}
}
}
}
}
}
}
}
}
}
else {
validate72.errors = [{instancePath,schemaPath:"#/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
validate72.errors = vErrors;
return errors === 0;
}
validate72.evaluated = {"props":true,"dynamicProps":false,"dynamicItems":false};


function validate71(data, {instancePath="", parentData, parentDataProperty, rootData=data, dynamicAnchors={}}={}){
let vErrors = null;
let errors = 0;
const evaluated0 = validate71.evaluated;
if(evaluated0.dynamicProps){
evaluated0.props = undefined;
}
if(evaluated0.dynamicItems){
evaluated0.items = undefined;
}
if(errors === 0){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing0;
if(((((data.files === undefined) && (missing0 = "files")) || ((data.quota_bytes === undefined) && (missing0 = "quota_bytes"))) || ((data.used_bytes === undefined) && (missing0 = "used_bytes"))) || ((data.retention_days === undefined) && (missing0 = "retention_days"))){
validate71.errors = [{instancePath,schemaPath:"#/required",keyword:"required",params:{missingProperty: missing0},message:"must have required property '"+missing0+"'"}];
return false;
}
else {
const _errs1 = errors;
for(const key0 in data){
if(!((((key0 === "files") || (key0 === "quota_bytes")) || (key0 === "retention_days")) || (key0 === "used_bytes"))){
validate71.errors = [{instancePath,schemaPath:"#/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key0},message:"must NOT have additional properties"}];
return false;
break;
}
}
if(_errs1 === errors){
if(data.files !== undefined){
let data0 = data.files;
const _errs2 = errors;
if(errors === _errs2){
if(Array.isArray(data0)){
var valid1 = true;
const len0 = data0.length;
for(let i0=0; i0<len0; i0++){
const _errs4 = errors;
if(!(validate72(data0[i0], {instancePath:instancePath+"/files/" + i0,parentData:data0,parentDataProperty:i0,rootData,dynamicAnchors}))){
vErrors = vErrors === null ? validate72.errors : vErrors.concat(validate72.errors);
errors = vErrors.length;
}
var valid1 = _errs4 === errors;
if(!valid1){
break;
}
}
}
else {
validate71.errors = [{instancePath:instancePath+"/files",schemaPath:"#/properties/files/type",keyword:"type",params:{type: "array"},message:"must be array"}];
return false;
}
}
var valid0 = _errs2 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.quota_bytes !== undefined){
const _errs5 = errors;
if(typeof data.quota_bytes !== "string"){
validate71.errors = [{instancePath:instancePath+"/quota_bytes",schemaPath:"#/properties/quota_bytes/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs5 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.retention_days !== undefined){
let data3 = data.retention_days;
const _errs7 = errors;
if(!(((typeof data3 == "number") && (!(data3 % 1) && !isNaN(data3))) && (isFinite(data3)))){
validate71.errors = [{instancePath:instancePath+"/retention_days",schemaPath:"#/properties/retention_days/type",keyword:"type",params:{type: "integer"},message:"must be integer"}];
return false;
}
if(errors === _errs7){
if((typeof data3 == "number") && (isFinite(data3))){
if(data3 > 65535 || isNaN(data3)){
validate71.errors = [{instancePath:instancePath+"/retention_days",schemaPath:"#/properties/retention_days/maximum",keyword:"maximum",params:{comparison: "<=", limit: 65535},message:"must be <= 65535"}];
return false;
}
else {
if(data3 < 0 || isNaN(data3)){
validate71.errors = [{instancePath:instancePath+"/retention_days",schemaPath:"#/properties/retention_days/minimum",keyword:"minimum",params:{comparison: ">=", limit: 0},message:"must be >= 0"}];
return false;
}
}
}
}
var valid0 = _errs7 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.used_bytes !== undefined){
const _errs9 = errors;
if(typeof data.used_bytes !== "string"){
validate71.errors = [{instancePath:instancePath+"/used_bytes",schemaPath:"#/properties/used_bytes/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs9 === errors;
}
else {
var valid0 = true;
}
}
}
}
}
}
}
else {
validate71.errors = [{instancePath,schemaPath:"#/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
validate71.errors = vErrors;
return errors === 0;
}
validate71.evaluated = {"props":true,"dynamicProps":false,"dynamicItems":false};

const schema80 = {"properties":{"activity":{"default":null,"items":{"$ref":"#/$defs/Activity"},"type":["array","null"]},"commandHistory":{"items":{"type":"string"},"type":"array"},"conversations":{"items":{"$ref":"#/$defs/Conversation"},"type":"array"},"inputHistory":{"items":{"$ref":"#/$defs/InputHistoryEntry"},"type":"array"},"instance":{"$ref":"#/$defs/InstanceInfo"},"operations":{"default":null,"items":{"$ref":"#/$defs/OperationDetail"},"type":["array","null"]},"presenceEnabled":{"default":null,"type":["boolean","null"]},"providerErrors":{"default":[],"items":{"$ref":"#/$defs/ProviderStatus"},"type":"array"},"revision":{"type":"string"}},"required":["instance","revision","conversations","commandHistory","inputHistory"],"type":"object"};
const schema81 = {"description":"Authenticated state changes observed by this profile, retained before publication.","properties":{"conversation":{"type":"string"},"id":{"type":"string"},"kind":{"type":"string"},"text":{"type":"string"},"timestamp":{"format":"uint64","minimum":0,"type":"integer"}},"required":["id","conversation","kind","text","timestamp"],"type":"object"};
const schema86 = {"properties":{"conversation":{"type":["string","null"]},"text":{"type":"string"}},"required":["text"],"type":"object"};
const schema92 = {"properties":{"code":{"type":"string"},"id":{"type":"string"},"message":{"type":"string"},"retryable":{"type":"boolean"}},"required":["id","code","message","retryable"],"type":"object"};
const schema82 = {"properties":{"active":{"type":"boolean"},"channelId":{"type":"string"},"commands":{"default":[],"items":{"$ref":"#/$defs/CommandSpec"},"type":"array"},"directory":{"default":null,"type":["string","null"]},"id":{"type":"string"},"inputLimitBytes":{"default":12000,"format":"uint","minimum":0,"type":"integer"},"kind":{"$ref":"#/$defs/ConversationKind"},"lastMessageId":{"type":["string","null"]},"members":{"items":{"$ref":"#/$defs/Member"},"type":"array"},"name":{"type":"string"},"owner":{"type":"boolean"},"provider":{"default":null,"type":["string","null"]},"topic":{"type":"string"},"unread":{"format":"uint32","minimum":0,"type":"integer"},"visibility":{"default":null,"type":["string","null"]}},"required":["id","channelId","kind","name","topic","active","owner","members","unread"],"type":"object"};
const schema84 = {"enum":["channel","query","archive"],"type":"string"};
const schema85 = {"properties":{"capabilities":{"default":[],"items":{"type":"string"},"type":"array"},"id":{"type":"string"},"isSelf":{"type":"boolean"},"nickname":{"type":"string"},"recentlyActive":{"default":null,"type":["boolean","null"]}},"required":["id","nickname","isSelf"],"type":"object"};

function validate77(data, {instancePath="", parentData, parentDataProperty, rootData=data, dynamicAnchors={}}={}){
let vErrors = null;
let errors = 0;
const evaluated0 = validate77.evaluated;
if(evaluated0.dynamicProps){
evaluated0.props = undefined;
}
if(evaluated0.dynamicItems){
evaluated0.items = undefined;
}
if(errors === 0){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing0;
if((((((((((data.id === undefined) && (missing0 = "id")) || ((data.channelId === undefined) && (missing0 = "channelId"))) || ((data.kind === undefined) && (missing0 = "kind"))) || ((data.name === undefined) && (missing0 = "name"))) || ((data.topic === undefined) && (missing0 = "topic"))) || ((data.active === undefined) && (missing0 = "active"))) || ((data.owner === undefined) && (missing0 = "owner"))) || ((data.members === undefined) && (missing0 = "members"))) || ((data.unread === undefined) && (missing0 = "unread"))){
validate77.errors = [{instancePath,schemaPath:"#/required",keyword:"required",params:{missingProperty: missing0},message:"must have required property '"+missing0+"'"}];
return false;
}
else {
if(data.active !== undefined){
const _errs1 = errors;
if(typeof data.active !== "boolean"){
validate77.errors = [{instancePath:instancePath+"/active",schemaPath:"#/properties/active/type",keyword:"type",params:{type: "boolean"},message:"must be boolean"}];
return false;
}
var valid0 = _errs1 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.channelId !== undefined){
const _errs3 = errors;
if(typeof data.channelId !== "string"){
validate77.errors = [{instancePath:instancePath+"/channelId",schemaPath:"#/properties/channelId/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs3 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.commands !== undefined){
let data2 = data.commands;
const _errs5 = errors;
if(errors === _errs5){
if(Array.isArray(data2)){
var valid1 = true;
const len0 = data2.length;
for(let i0=0; i0<len0; i0++){
let data3 = data2[i0];
const _errs7 = errors;
const _errs8 = errors;
if(errors === _errs8){
if(data3 && typeof data3 == "object" && !Array.isArray(data3)){
let missing1;
if((((((data3.name === undefined) && (missing1 = "name")) || ((data3.usage === undefined) && (missing1 = "usage"))) || ((data3.description === undefined) && (missing1 = "description"))) || ((data3.scope === undefined) && (missing1 = "scope"))) || ((data3.available === undefined) && (missing1 = "available"))){
validate77.errors = [{instancePath:instancePath+"/commands/" + i0,schemaPath:"#/$defs/CommandSpec/required",keyword:"required",params:{missingProperty: missing1},message:"must have required property '"+missing1+"'"}];
return false;
}
else {
if(data3.available !== undefined){
const _errs10 = errors;
if(typeof data3.available !== "boolean"){
validate77.errors = [{instancePath:instancePath+"/commands/" + i0+"/available",schemaPath:"#/$defs/CommandSpec/properties/available/type",keyword:"type",params:{type: "boolean"},message:"must be boolean"}];
return false;
}
var valid3 = _errs10 === errors;
}
else {
var valid3 = true;
}
if(valid3){
if(data3.capability !== undefined){
let data5 = data3.capability;
const _errs12 = errors;
if((typeof data5 !== "string") && (data5 !== null)){
validate77.errors = [{instancePath:instancePath+"/commands/" + i0+"/capability",schemaPath:"#/$defs/CommandSpec/properties/capability/type",keyword:"type",params:{type: schema83.properties.capability.type},message:"must be string,null"}];
return false;
}
var valid3 = _errs12 === errors;
}
else {
var valid3 = true;
}
if(valid3){
if(data3.description !== undefined){
const _errs14 = errors;
if(typeof data3.description !== "string"){
validate77.errors = [{instancePath:instancePath+"/commands/" + i0+"/description",schemaPath:"#/$defs/CommandSpec/properties/description/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid3 = _errs14 === errors;
}
else {
var valid3 = true;
}
if(valid3){
if(data3.name !== undefined){
const _errs16 = errors;
if(typeof data3.name !== "string"){
validate77.errors = [{instancePath:instancePath+"/commands/" + i0+"/name",schemaPath:"#/$defs/CommandSpec/properties/name/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid3 = _errs16 === errors;
}
else {
var valid3 = true;
}
if(valid3){
if(data3.scope !== undefined){
const _errs18 = errors;
if(typeof data3.scope !== "string"){
validate77.errors = [{instancePath:instancePath+"/commands/" + i0+"/scope",schemaPath:"#/$defs/CommandSpec/properties/scope/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid3 = _errs18 === errors;
}
else {
var valid3 = true;
}
if(valid3){
if(data3.usage !== undefined){
const _errs20 = errors;
if(typeof data3.usage !== "string"){
validate77.errors = [{instancePath:instancePath+"/commands/" + i0+"/usage",schemaPath:"#/$defs/CommandSpec/properties/usage/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid3 = _errs20 === errors;
}
else {
var valid3 = true;
}
}
}
}
}
}
}
}
else {
validate77.errors = [{instancePath:instancePath+"/commands/" + i0,schemaPath:"#/$defs/CommandSpec/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
var valid1 = _errs7 === errors;
if(!valid1){
break;
}
}
}
else {
validate77.errors = [{instancePath:instancePath+"/commands",schemaPath:"#/properties/commands/type",keyword:"type",params:{type: "array"},message:"must be array"}];
return false;
}
}
var valid0 = _errs5 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.directory !== undefined){
let data10 = data.directory;
const _errs22 = errors;
if((typeof data10 !== "string") && (data10 !== null)){
validate77.errors = [{instancePath:instancePath+"/directory",schemaPath:"#/properties/directory/type",keyword:"type",params:{type: schema82.properties.directory.type},message:"must be string,null"}];
return false;
}
var valid0 = _errs22 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.id !== undefined){
const _errs24 = errors;
if(typeof data.id !== "string"){
validate77.errors = [{instancePath:instancePath+"/id",schemaPath:"#/properties/id/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs24 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.inputLimitBytes !== undefined){
let data12 = data.inputLimitBytes;
const _errs26 = errors;
if(!(((typeof data12 == "number") && (!(data12 % 1) && !isNaN(data12))) && (isFinite(data12)))){
validate77.errors = [{instancePath:instancePath+"/inputLimitBytes",schemaPath:"#/properties/inputLimitBytes/type",keyword:"type",params:{type: "integer"},message:"must be integer"}];
return false;
}
if(errors === _errs26){
if((typeof data12 == "number") && (isFinite(data12))){
if(data12 < 0 || isNaN(data12)){
validate77.errors = [{instancePath:instancePath+"/inputLimitBytes",schemaPath:"#/properties/inputLimitBytes/minimum",keyword:"minimum",params:{comparison: ">=", limit: 0},message:"must be >= 0"}];
return false;
}
}
}
var valid0 = _errs26 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.kind !== undefined){
let data13 = data.kind;
const _errs28 = errors;
if(typeof data13 !== "string"){
validate77.errors = [{instancePath:instancePath+"/kind",schemaPath:"#/$defs/ConversationKind/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
if(!(((data13 === "channel") || (data13 === "query")) || (data13 === "archive"))){
validate77.errors = [{instancePath:instancePath+"/kind",schemaPath:"#/$defs/ConversationKind/enum",keyword:"enum",params:{allowedValues: schema84.enum},message:"must be equal to one of the allowed values"}];
return false;
}
var valid0 = _errs28 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.lastMessageId !== undefined){
let data14 = data.lastMessageId;
const _errs31 = errors;
if((typeof data14 !== "string") && (data14 !== null)){
validate77.errors = [{instancePath:instancePath+"/lastMessageId",schemaPath:"#/properties/lastMessageId/type",keyword:"type",params:{type: schema82.properties.lastMessageId.type},message:"must be string,null"}];
return false;
}
var valid0 = _errs31 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.members !== undefined){
let data15 = data.members;
const _errs33 = errors;
if(errors === _errs33){
if(Array.isArray(data15)){
var valid5 = true;
const len1 = data15.length;
for(let i1=0; i1<len1; i1++){
let data16 = data15[i1];
const _errs35 = errors;
const _errs36 = errors;
if(errors === _errs36){
if(data16 && typeof data16 == "object" && !Array.isArray(data16)){
let missing2;
if((((data16.id === undefined) && (missing2 = "id")) || ((data16.nickname === undefined) && (missing2 = "nickname"))) || ((data16.isSelf === undefined) && (missing2 = "isSelf"))){
validate77.errors = [{instancePath:instancePath+"/members/" + i1,schemaPath:"#/$defs/Member/required",keyword:"required",params:{missingProperty: missing2},message:"must have required property '"+missing2+"'"}];
return false;
}
else {
if(data16.capabilities !== undefined){
let data17 = data16.capabilities;
const _errs38 = errors;
if(errors === _errs38){
if(Array.isArray(data17)){
var valid8 = true;
const len2 = data17.length;
for(let i2=0; i2<len2; i2++){
const _errs40 = errors;
if(typeof data17[i2] !== "string"){
validate77.errors = [{instancePath:instancePath+"/members/" + i1+"/capabilities/" + i2,schemaPath:"#/$defs/Member/properties/capabilities/items/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid8 = _errs40 === errors;
if(!valid8){
break;
}
}
}
else {
validate77.errors = [{instancePath:instancePath+"/members/" + i1+"/capabilities",schemaPath:"#/$defs/Member/properties/capabilities/type",keyword:"type",params:{type: "array"},message:"must be array"}];
return false;
}
}
var valid7 = _errs38 === errors;
}
else {
var valid7 = true;
}
if(valid7){
if(data16.id !== undefined){
const _errs42 = errors;
if(typeof data16.id !== "string"){
validate77.errors = [{instancePath:instancePath+"/members/" + i1+"/id",schemaPath:"#/$defs/Member/properties/id/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid7 = _errs42 === errors;
}
else {
var valid7 = true;
}
if(valid7){
if(data16.isSelf !== undefined){
const _errs44 = errors;
if(typeof data16.isSelf !== "boolean"){
validate77.errors = [{instancePath:instancePath+"/members/" + i1+"/isSelf",schemaPath:"#/$defs/Member/properties/isSelf/type",keyword:"type",params:{type: "boolean"},message:"must be boolean"}];
return false;
}
var valid7 = _errs44 === errors;
}
else {
var valid7 = true;
}
if(valid7){
if(data16.nickname !== undefined){
const _errs46 = errors;
if(typeof data16.nickname !== "string"){
validate77.errors = [{instancePath:instancePath+"/members/" + i1+"/nickname",schemaPath:"#/$defs/Member/properties/nickname/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid7 = _errs46 === errors;
}
else {
var valid7 = true;
}
if(valid7){
if(data16.recentlyActive !== undefined){
let data22 = data16.recentlyActive;
const _errs48 = errors;
if((typeof data22 !== "boolean") && (data22 !== null)){
validate77.errors = [{instancePath:instancePath+"/members/" + i1+"/recentlyActive",schemaPath:"#/$defs/Member/properties/recentlyActive/type",keyword:"type",params:{type: schema85.properties.recentlyActive.type},message:"must be boolean,null"}];
return false;
}
var valid7 = _errs48 === errors;
}
else {
var valid7 = true;
}
}
}
}
}
}
}
else {
validate77.errors = [{instancePath:instancePath+"/members/" + i1,schemaPath:"#/$defs/Member/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
var valid5 = _errs35 === errors;
if(!valid5){
break;
}
}
}
else {
validate77.errors = [{instancePath:instancePath+"/members",schemaPath:"#/properties/members/type",keyword:"type",params:{type: "array"},message:"must be array"}];
return false;
}
}
var valid0 = _errs33 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.name !== undefined){
const _errs50 = errors;
if(typeof data.name !== "string"){
validate77.errors = [{instancePath:instancePath+"/name",schemaPath:"#/properties/name/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs50 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.owner !== undefined){
const _errs52 = errors;
if(typeof data.owner !== "boolean"){
validate77.errors = [{instancePath:instancePath+"/owner",schemaPath:"#/properties/owner/type",keyword:"type",params:{type: "boolean"},message:"must be boolean"}];
return false;
}
var valid0 = _errs52 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.provider !== undefined){
let data25 = data.provider;
const _errs54 = errors;
if((typeof data25 !== "string") && (data25 !== null)){
validate77.errors = [{instancePath:instancePath+"/provider",schemaPath:"#/properties/provider/type",keyword:"type",params:{type: schema82.properties.provider.type},message:"must be string,null"}];
return false;
}
var valid0 = _errs54 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.topic !== undefined){
const _errs56 = errors;
if(typeof data.topic !== "string"){
validate77.errors = [{instancePath:instancePath+"/topic",schemaPath:"#/properties/topic/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs56 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.unread !== undefined){
let data27 = data.unread;
const _errs58 = errors;
if(!(((typeof data27 == "number") && (!(data27 % 1) && !isNaN(data27))) && (isFinite(data27)))){
validate77.errors = [{instancePath:instancePath+"/unread",schemaPath:"#/properties/unread/type",keyword:"type",params:{type: "integer"},message:"must be integer"}];
return false;
}
if(errors === _errs58){
if((typeof data27 == "number") && (isFinite(data27))){
if(data27 < 0 || isNaN(data27)){
validate77.errors = [{instancePath:instancePath+"/unread",schemaPath:"#/properties/unread/minimum",keyword:"minimum",params:{comparison: ">=", limit: 0},message:"must be >= 0"}];
return false;
}
}
}
var valid0 = _errs58 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.visibility !== undefined){
let data28 = data.visibility;
const _errs60 = errors;
if((typeof data28 !== "string") && (data28 !== null)){
validate77.errors = [{instancePath:instancePath+"/visibility",schemaPath:"#/properties/visibility/type",keyword:"type",params:{type: schema82.properties.visibility.type},message:"must be string,null"}];
return false;
}
var valid0 = _errs60 === errors;
}
else {
var valid0 = true;
}
}
}
}
}
}
}
}
}
}
}
}
}
}
}
}
}
else {
validate77.errors = [{instancePath,schemaPath:"#/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
validate77.errors = vErrors;
return errors === 0;
}
validate77.evaluated = {"props":{"active":true,"channelId":true,"commands":true,"directory":true,"id":true,"inputLimitBytes":true,"kind":true,"lastMessageId":true,"members":true,"name":true,"owner":true,"provider":true,"topic":true,"unread":true,"visibility":true},"dynamicProps":false,"dynamicItems":false};

const schema88 = {"description":"Safe metadata plus the protected result retained in the encrypted operation journal.","properties":{"action":{"type":"string"},"conversation":{"type":["string","null"]},"id":{"type":"string"},"instance":{"type":"string"},"message":{"type":["string","null"]},"network":{"default":null,"type":["string","null"]},"output":{"anyOf":[{"$ref":"#/$defs/CommandOutput"},{"type":"null"}]},"started":{"format":"uint64","minimum":0,"type":"integer"},"state":{"type":"string"}},"required":["id","instance","action","started","state"],"type":"object"};
const schema89 = {"oneOf":[{"properties":{"commands":{"items":{"$ref":"#/$defs/CommandSpec"},"type":"array"},"kind":{"const":"help","type":"string"}},"required":["kind","commands"],"type":"object"},{"properties":{"channels":{"items":{"$ref":"#/$defs/DirectoryEntry"},"type":"array"},"kind":{"const":"directory","type":"string"}},"required":["kind","channels"],"type":"object"},{"properties":{"channel":{"type":"string"},"expires":{"format":"uint64","minimum":0,"type":"integer"},"kind":{"const":"invitation","type":"string"},"link":{"type":"string"},"localOnly":{"default":false,"type":"boolean"}},"required":["kind","channel","link","expires"],"type":"object"},{"properties":{"kind":{"const":"text","type":"string"},"text":{"type":"string"},"title":{"type":"string"}},"required":["kind","title","text"],"type":"object"},{"properties":{"kind":{"const":"status","type":"string"},"text":{"type":"string"}},"required":["kind","text"],"type":"object"},{"properties":{"conversation":{"type":"string"},"kind":{"const":"close","type":"string"}},"required":["kind","conversation"],"type":"object"}]};
const schema91 = {"properties":{"conversation":{"type":["string","null"]},"joined":{"type":"boolean"},"name":{"type":"string"}},"required":["name","joined"],"type":"object"};

function validate80(data, {instancePath="", parentData, parentDataProperty, rootData=data, dynamicAnchors={}}={}){
let vErrors = null;
let errors = 0;
const evaluated0 = validate80.evaluated;
if(evaluated0.dynamicProps){
evaluated0.props = undefined;
}
if(evaluated0.dynamicItems){
evaluated0.items = undefined;
}
const _errs0 = errors;
let valid0 = false;
let passing0 = null;
const _errs1 = errors;
if(errors === _errs1){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing0;
if(((data.kind === undefined) && (missing0 = "kind")) || ((data.commands === undefined) && (missing0 = "commands"))){
const err0 = {instancePath,schemaPath:"#/oneOf/0/required",keyword:"required",params:{missingProperty: missing0},message:"must have required property '"+missing0+"'"};
if(vErrors === null){
vErrors = [err0];
}
else {
vErrors.push(err0);
}
errors++;
}
else {
if(data.commands !== undefined){
let data0 = data.commands;
const _errs3 = errors;
if(errors === _errs3){
if(Array.isArray(data0)){
var valid2 = true;
const len0 = data0.length;
for(let i0=0; i0<len0; i0++){
let data1 = data0[i0];
const _errs5 = errors;
const _errs6 = errors;
if(errors === _errs6){
if(data1 && typeof data1 == "object" && !Array.isArray(data1)){
let missing1;
if((((((data1.name === undefined) && (missing1 = "name")) || ((data1.usage === undefined) && (missing1 = "usage"))) || ((data1.description === undefined) && (missing1 = "description"))) || ((data1.scope === undefined) && (missing1 = "scope"))) || ((data1.available === undefined) && (missing1 = "available"))){
const err1 = {instancePath:instancePath+"/commands/" + i0,schemaPath:"#/$defs/CommandSpec/required",keyword:"required",params:{missingProperty: missing1},message:"must have required property '"+missing1+"'"};
if(vErrors === null){
vErrors = [err1];
}
else {
vErrors.push(err1);
}
errors++;
}
else {
if(data1.available !== undefined){
const _errs8 = errors;
if(typeof data1.available !== "boolean"){
const err2 = {instancePath:instancePath+"/commands/" + i0+"/available",schemaPath:"#/$defs/CommandSpec/properties/available/type",keyword:"type",params:{type: "boolean"},message:"must be boolean"};
if(vErrors === null){
vErrors = [err2];
}
else {
vErrors.push(err2);
}
errors++;
}
var valid4 = _errs8 === errors;
}
else {
var valid4 = true;
}
if(valid4){
if(data1.capability !== undefined){
let data3 = data1.capability;
const _errs10 = errors;
if((typeof data3 !== "string") && (data3 !== null)){
const err3 = {instancePath:instancePath+"/commands/" + i0+"/capability",schemaPath:"#/$defs/CommandSpec/properties/capability/type",keyword:"type",params:{type: schema83.properties.capability.type},message:"must be string,null"};
if(vErrors === null){
vErrors = [err3];
}
else {
vErrors.push(err3);
}
errors++;
}
var valid4 = _errs10 === errors;
}
else {
var valid4 = true;
}
if(valid4){
if(data1.description !== undefined){
const _errs12 = errors;
if(typeof data1.description !== "string"){
const err4 = {instancePath:instancePath+"/commands/" + i0+"/description",schemaPath:"#/$defs/CommandSpec/properties/description/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err4];
}
else {
vErrors.push(err4);
}
errors++;
}
var valid4 = _errs12 === errors;
}
else {
var valid4 = true;
}
if(valid4){
if(data1.name !== undefined){
const _errs14 = errors;
if(typeof data1.name !== "string"){
const err5 = {instancePath:instancePath+"/commands/" + i0+"/name",schemaPath:"#/$defs/CommandSpec/properties/name/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err5];
}
else {
vErrors.push(err5);
}
errors++;
}
var valid4 = _errs14 === errors;
}
else {
var valid4 = true;
}
if(valid4){
if(data1.scope !== undefined){
const _errs16 = errors;
if(typeof data1.scope !== "string"){
const err6 = {instancePath:instancePath+"/commands/" + i0+"/scope",schemaPath:"#/$defs/CommandSpec/properties/scope/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err6];
}
else {
vErrors.push(err6);
}
errors++;
}
var valid4 = _errs16 === errors;
}
else {
var valid4 = true;
}
if(valid4){
if(data1.usage !== undefined){
const _errs18 = errors;
if(typeof data1.usage !== "string"){
const err7 = {instancePath:instancePath+"/commands/" + i0+"/usage",schemaPath:"#/$defs/CommandSpec/properties/usage/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err7];
}
else {
vErrors.push(err7);
}
errors++;
}
var valid4 = _errs18 === errors;
}
else {
var valid4 = true;
}
}
}
}
}
}
}
}
else {
const err8 = {instancePath:instancePath+"/commands/" + i0,schemaPath:"#/$defs/CommandSpec/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err8];
}
else {
vErrors.push(err8);
}
errors++;
}
}
var valid2 = _errs5 === errors;
if(!valid2){
break;
}
}
}
else {
const err9 = {instancePath:instancePath+"/commands",schemaPath:"#/oneOf/0/properties/commands/type",keyword:"type",params:{type: "array"},message:"must be array"};
if(vErrors === null){
vErrors = [err9];
}
else {
vErrors.push(err9);
}
errors++;
}
}
var valid1 = _errs3 === errors;
}
else {
var valid1 = true;
}
if(valid1){
if(data.kind !== undefined){
let data8 = data.kind;
const _errs20 = errors;
if(typeof data8 !== "string"){
const err10 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/0/properties/kind/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err10];
}
else {
vErrors.push(err10);
}
errors++;
}
if("help" !== data8){
const err11 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/0/properties/kind/const",keyword:"const",params:{allowedValue: "help"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err11];
}
else {
vErrors.push(err11);
}
errors++;
}
var valid1 = _errs20 === errors;
}
else {
var valid1 = true;
}
}
}
}
else {
const err12 = {instancePath,schemaPath:"#/oneOf/0/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err12];
}
else {
vErrors.push(err12);
}
errors++;
}
}
var _valid0 = _errs1 === errors;
if(_valid0){
valid0 = true;
passing0 = 0;
var props0 = {};
props0.commands = true;
props0.kind = true;
}
const _errs22 = errors;
if(errors === _errs22){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing2;
if(((data.kind === undefined) && (missing2 = "kind")) || ((data.channels === undefined) && (missing2 = "channels"))){
const err13 = {instancePath,schemaPath:"#/oneOf/1/required",keyword:"required",params:{missingProperty: missing2},message:"must have required property '"+missing2+"'"};
if(vErrors === null){
vErrors = [err13];
}
else {
vErrors.push(err13);
}
errors++;
}
else {
if(data.channels !== undefined){
let data9 = data.channels;
const _errs24 = errors;
if(errors === _errs24){
if(Array.isArray(data9)){
var valid6 = true;
const len1 = data9.length;
for(let i1=0; i1<len1; i1++){
let data10 = data9[i1];
const _errs26 = errors;
const _errs27 = errors;
if(errors === _errs27){
if(data10 && typeof data10 == "object" && !Array.isArray(data10)){
let missing3;
if(((data10.name === undefined) && (missing3 = "name")) || ((data10.joined === undefined) && (missing3 = "joined"))){
const err14 = {instancePath:instancePath+"/channels/" + i1,schemaPath:"#/$defs/DirectoryEntry/required",keyword:"required",params:{missingProperty: missing3},message:"must have required property '"+missing3+"'"};
if(vErrors === null){
vErrors = [err14];
}
else {
vErrors.push(err14);
}
errors++;
}
else {
if(data10.conversation !== undefined){
let data11 = data10.conversation;
const _errs29 = errors;
if((typeof data11 !== "string") && (data11 !== null)){
const err15 = {instancePath:instancePath+"/channels/" + i1+"/conversation",schemaPath:"#/$defs/DirectoryEntry/properties/conversation/type",keyword:"type",params:{type: schema91.properties.conversation.type},message:"must be string,null"};
if(vErrors === null){
vErrors = [err15];
}
else {
vErrors.push(err15);
}
errors++;
}
var valid8 = _errs29 === errors;
}
else {
var valid8 = true;
}
if(valid8){
if(data10.joined !== undefined){
const _errs31 = errors;
if(typeof data10.joined !== "boolean"){
const err16 = {instancePath:instancePath+"/channels/" + i1+"/joined",schemaPath:"#/$defs/DirectoryEntry/properties/joined/type",keyword:"type",params:{type: "boolean"},message:"must be boolean"};
if(vErrors === null){
vErrors = [err16];
}
else {
vErrors.push(err16);
}
errors++;
}
var valid8 = _errs31 === errors;
}
else {
var valid8 = true;
}
if(valid8){
if(data10.name !== undefined){
const _errs33 = errors;
if(typeof data10.name !== "string"){
const err17 = {instancePath:instancePath+"/channels/" + i1+"/name",schemaPath:"#/$defs/DirectoryEntry/properties/name/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err17];
}
else {
vErrors.push(err17);
}
errors++;
}
var valid8 = _errs33 === errors;
}
else {
var valid8 = true;
}
}
}
}
}
else {
const err18 = {instancePath:instancePath+"/channels/" + i1,schemaPath:"#/$defs/DirectoryEntry/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err18];
}
else {
vErrors.push(err18);
}
errors++;
}
}
var valid6 = _errs26 === errors;
if(!valid6){
break;
}
}
}
else {
const err19 = {instancePath:instancePath+"/channels",schemaPath:"#/oneOf/1/properties/channels/type",keyword:"type",params:{type: "array"},message:"must be array"};
if(vErrors === null){
vErrors = [err19];
}
else {
vErrors.push(err19);
}
errors++;
}
}
var valid5 = _errs24 === errors;
}
else {
var valid5 = true;
}
if(valid5){
if(data.kind !== undefined){
let data14 = data.kind;
const _errs35 = errors;
if(typeof data14 !== "string"){
const err20 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/1/properties/kind/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err20];
}
else {
vErrors.push(err20);
}
errors++;
}
if("directory" !== data14){
const err21 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/1/properties/kind/const",keyword:"const",params:{allowedValue: "directory"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err21];
}
else {
vErrors.push(err21);
}
errors++;
}
var valid5 = _errs35 === errors;
}
else {
var valid5 = true;
}
}
}
}
else {
const err22 = {instancePath,schemaPath:"#/oneOf/1/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err22];
}
else {
vErrors.push(err22);
}
errors++;
}
}
var _valid0 = _errs22 === errors;
if(_valid0 && valid0){
valid0 = false;
passing0 = [passing0, 1];
}
else {
if(_valid0){
valid0 = true;
passing0 = 1;
if(props0 !== true){
props0 = props0 || {};
props0.channels = true;
props0.kind = true;
}
}
const _errs37 = errors;
if(errors === _errs37){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing4;
if(((((data.kind === undefined) && (missing4 = "kind")) || ((data.channel === undefined) && (missing4 = "channel"))) || ((data.link === undefined) && (missing4 = "link"))) || ((data.expires === undefined) && (missing4 = "expires"))){
const err23 = {instancePath,schemaPath:"#/oneOf/2/required",keyword:"required",params:{missingProperty: missing4},message:"must have required property '"+missing4+"'"};
if(vErrors === null){
vErrors = [err23];
}
else {
vErrors.push(err23);
}
errors++;
}
else {
if(data.channel !== undefined){
const _errs39 = errors;
if(typeof data.channel !== "string"){
const err24 = {instancePath:instancePath+"/channel",schemaPath:"#/oneOf/2/properties/channel/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err24];
}
else {
vErrors.push(err24);
}
errors++;
}
var valid9 = _errs39 === errors;
}
else {
var valid9 = true;
}
if(valid9){
if(data.expires !== undefined){
let data16 = data.expires;
const _errs41 = errors;
if(!(((typeof data16 == "number") && (!(data16 % 1) && !isNaN(data16))) && (isFinite(data16)))){
const err25 = {instancePath:instancePath+"/expires",schemaPath:"#/oneOf/2/properties/expires/type",keyword:"type",params:{type: "integer"},message:"must be integer"};
if(vErrors === null){
vErrors = [err25];
}
else {
vErrors.push(err25);
}
errors++;
}
if(errors === _errs41){
if((typeof data16 == "number") && (isFinite(data16))){
if(data16 < 0 || isNaN(data16)){
const err26 = {instancePath:instancePath+"/expires",schemaPath:"#/oneOf/2/properties/expires/minimum",keyword:"minimum",params:{comparison: ">=", limit: 0},message:"must be >= 0"};
if(vErrors === null){
vErrors = [err26];
}
else {
vErrors.push(err26);
}
errors++;
}
}
}
var valid9 = _errs41 === errors;
}
else {
var valid9 = true;
}
if(valid9){
if(data.kind !== undefined){
let data17 = data.kind;
const _errs43 = errors;
if(typeof data17 !== "string"){
const err27 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/2/properties/kind/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err27];
}
else {
vErrors.push(err27);
}
errors++;
}
if("invitation" !== data17){
const err28 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/2/properties/kind/const",keyword:"const",params:{allowedValue: "invitation"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err28];
}
else {
vErrors.push(err28);
}
errors++;
}
var valid9 = _errs43 === errors;
}
else {
var valid9 = true;
}
if(valid9){
if(data.link !== undefined){
const _errs45 = errors;
if(typeof data.link !== "string"){
const err29 = {instancePath:instancePath+"/link",schemaPath:"#/oneOf/2/properties/link/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err29];
}
else {
vErrors.push(err29);
}
errors++;
}
var valid9 = _errs45 === errors;
}
else {
var valid9 = true;
}
if(valid9){
if(data.localOnly !== undefined){
const _errs47 = errors;
if(typeof data.localOnly !== "boolean"){
const err30 = {instancePath:instancePath+"/localOnly",schemaPath:"#/oneOf/2/properties/localOnly/type",keyword:"type",params:{type: "boolean"},message:"must be boolean"};
if(vErrors === null){
vErrors = [err30];
}
else {
vErrors.push(err30);
}
errors++;
}
var valid9 = _errs47 === errors;
}
else {
var valid9 = true;
}
}
}
}
}
}
}
else {
const err31 = {instancePath,schemaPath:"#/oneOf/2/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err31];
}
else {
vErrors.push(err31);
}
errors++;
}
}
var _valid0 = _errs37 === errors;
if(_valid0 && valid0){
valid0 = false;
passing0 = [passing0, 2];
}
else {
if(_valid0){
valid0 = true;
passing0 = 2;
if(props0 !== true){
props0 = props0 || {};
props0.channel = true;
props0.expires = true;
props0.kind = true;
props0.link = true;
props0.localOnly = true;
}
}
const _errs49 = errors;
if(errors === _errs49){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing5;
if((((data.kind === undefined) && (missing5 = "kind")) || ((data.title === undefined) && (missing5 = "title"))) || ((data.text === undefined) && (missing5 = "text"))){
const err32 = {instancePath,schemaPath:"#/oneOf/3/required",keyword:"required",params:{missingProperty: missing5},message:"must have required property '"+missing5+"'"};
if(vErrors === null){
vErrors = [err32];
}
else {
vErrors.push(err32);
}
errors++;
}
else {
if(data.kind !== undefined){
let data20 = data.kind;
const _errs51 = errors;
if(typeof data20 !== "string"){
const err33 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/3/properties/kind/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err33];
}
else {
vErrors.push(err33);
}
errors++;
}
if("text" !== data20){
const err34 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/3/properties/kind/const",keyword:"const",params:{allowedValue: "text"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err34];
}
else {
vErrors.push(err34);
}
errors++;
}
var valid10 = _errs51 === errors;
}
else {
var valid10 = true;
}
if(valid10){
if(data.text !== undefined){
const _errs53 = errors;
if(typeof data.text !== "string"){
const err35 = {instancePath:instancePath+"/text",schemaPath:"#/oneOf/3/properties/text/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err35];
}
else {
vErrors.push(err35);
}
errors++;
}
var valid10 = _errs53 === errors;
}
else {
var valid10 = true;
}
if(valid10){
if(data.title !== undefined){
const _errs55 = errors;
if(typeof data.title !== "string"){
const err36 = {instancePath:instancePath+"/title",schemaPath:"#/oneOf/3/properties/title/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err36];
}
else {
vErrors.push(err36);
}
errors++;
}
var valid10 = _errs55 === errors;
}
else {
var valid10 = true;
}
}
}
}
}
else {
const err37 = {instancePath,schemaPath:"#/oneOf/3/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err37];
}
else {
vErrors.push(err37);
}
errors++;
}
}
var _valid0 = _errs49 === errors;
if(_valid0 && valid0){
valid0 = false;
passing0 = [passing0, 3];
}
else {
if(_valid0){
valid0 = true;
passing0 = 3;
if(props0 !== true){
props0 = props0 || {};
props0.kind = true;
props0.text = true;
props0.title = true;
}
}
const _errs57 = errors;
if(errors === _errs57){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing6;
if(((data.kind === undefined) && (missing6 = "kind")) || ((data.text === undefined) && (missing6 = "text"))){
const err38 = {instancePath,schemaPath:"#/oneOf/4/required",keyword:"required",params:{missingProperty: missing6},message:"must have required property '"+missing6+"'"};
if(vErrors === null){
vErrors = [err38];
}
else {
vErrors.push(err38);
}
errors++;
}
else {
if(data.kind !== undefined){
let data23 = data.kind;
const _errs59 = errors;
if(typeof data23 !== "string"){
const err39 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/4/properties/kind/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err39];
}
else {
vErrors.push(err39);
}
errors++;
}
if("status" !== data23){
const err40 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/4/properties/kind/const",keyword:"const",params:{allowedValue: "status"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err40];
}
else {
vErrors.push(err40);
}
errors++;
}
var valid11 = _errs59 === errors;
}
else {
var valid11 = true;
}
if(valid11){
if(data.text !== undefined){
const _errs61 = errors;
if(typeof data.text !== "string"){
const err41 = {instancePath:instancePath+"/text",schemaPath:"#/oneOf/4/properties/text/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err41];
}
else {
vErrors.push(err41);
}
errors++;
}
var valid11 = _errs61 === errors;
}
else {
var valid11 = true;
}
}
}
}
else {
const err42 = {instancePath,schemaPath:"#/oneOf/4/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err42];
}
else {
vErrors.push(err42);
}
errors++;
}
}
var _valid0 = _errs57 === errors;
if(_valid0 && valid0){
valid0 = false;
passing0 = [passing0, 4];
}
else {
if(_valid0){
valid0 = true;
passing0 = 4;
if(props0 !== true){
props0 = props0 || {};
props0.kind = true;
props0.text = true;
}
}
const _errs63 = errors;
if(errors === _errs63){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing7;
if(((data.kind === undefined) && (missing7 = "kind")) || ((data.conversation === undefined) && (missing7 = "conversation"))){
const err43 = {instancePath,schemaPath:"#/oneOf/5/required",keyword:"required",params:{missingProperty: missing7},message:"must have required property '"+missing7+"'"};
if(vErrors === null){
vErrors = [err43];
}
else {
vErrors.push(err43);
}
errors++;
}
else {
if(data.conversation !== undefined){
const _errs65 = errors;
if(typeof data.conversation !== "string"){
const err44 = {instancePath:instancePath+"/conversation",schemaPath:"#/oneOf/5/properties/conversation/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err44];
}
else {
vErrors.push(err44);
}
errors++;
}
var valid12 = _errs65 === errors;
}
else {
var valid12 = true;
}
if(valid12){
if(data.kind !== undefined){
let data26 = data.kind;
const _errs67 = errors;
if(typeof data26 !== "string"){
const err45 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/5/properties/kind/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err45];
}
else {
vErrors.push(err45);
}
errors++;
}
if("close" !== data26){
const err46 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/5/properties/kind/const",keyword:"const",params:{allowedValue: "close"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err46];
}
else {
vErrors.push(err46);
}
errors++;
}
var valid12 = _errs67 === errors;
}
else {
var valid12 = true;
}
}
}
}
else {
const err47 = {instancePath,schemaPath:"#/oneOf/5/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err47];
}
else {
vErrors.push(err47);
}
errors++;
}
}
var _valid0 = _errs63 === errors;
if(_valid0 && valid0){
valid0 = false;
passing0 = [passing0, 5];
}
else {
if(_valid0){
valid0 = true;
passing0 = 5;
if(props0 !== true){
props0 = props0 || {};
props0.conversation = true;
props0.kind = true;
}
}
}
}
}
}
}
if(!valid0){
const err48 = {instancePath,schemaPath:"#/oneOf",keyword:"oneOf",params:{passingSchemas: passing0},message:"must match exactly one schema in oneOf"};
if(vErrors === null){
vErrors = [err48];
}
else {
vErrors.push(err48);
}
errors++;
validate80.errors = vErrors;
return false;
}
else {
errors = _errs0;
if(vErrors !== null){
if(_errs0){
vErrors.length = _errs0;
}
else {
vErrors = null;
}
}
}
validate80.errors = vErrors;
evaluated0.props = props0;
return errors === 0;
}
validate80.evaluated = {"dynamicProps":true,"dynamicItems":false};


function validate79(data, {instancePath="", parentData, parentDataProperty, rootData=data, dynamicAnchors={}}={}){
let vErrors = null;
let errors = 0;
const evaluated0 = validate79.evaluated;
if(evaluated0.dynamicProps){
evaluated0.props = undefined;
}
if(evaluated0.dynamicItems){
evaluated0.items = undefined;
}
if(errors === 0){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing0;
if((((((data.id === undefined) && (missing0 = "id")) || ((data.instance === undefined) && (missing0 = "instance"))) || ((data.action === undefined) && (missing0 = "action"))) || ((data.started === undefined) && (missing0 = "started"))) || ((data.state === undefined) && (missing0 = "state"))){
validate79.errors = [{instancePath,schemaPath:"#/required",keyword:"required",params:{missingProperty: missing0},message:"must have required property '"+missing0+"'"}];
return false;
}
else {
if(data.action !== undefined){
const _errs1 = errors;
if(typeof data.action !== "string"){
validate79.errors = [{instancePath:instancePath+"/action",schemaPath:"#/properties/action/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs1 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.conversation !== undefined){
let data1 = data.conversation;
const _errs3 = errors;
if((typeof data1 !== "string") && (data1 !== null)){
validate79.errors = [{instancePath:instancePath+"/conversation",schemaPath:"#/properties/conversation/type",keyword:"type",params:{type: schema88.properties.conversation.type},message:"must be string,null"}];
return false;
}
var valid0 = _errs3 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.id !== undefined){
const _errs5 = errors;
if(typeof data.id !== "string"){
validate79.errors = [{instancePath:instancePath+"/id",schemaPath:"#/properties/id/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs5 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.instance !== undefined){
const _errs7 = errors;
if(typeof data.instance !== "string"){
validate79.errors = [{instancePath:instancePath+"/instance",schemaPath:"#/properties/instance/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs7 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.message !== undefined){
let data4 = data.message;
const _errs9 = errors;
if((typeof data4 !== "string") && (data4 !== null)){
validate79.errors = [{instancePath:instancePath+"/message",schemaPath:"#/properties/message/type",keyword:"type",params:{type: schema88.properties.message.type},message:"must be string,null"}];
return false;
}
var valid0 = _errs9 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.network !== undefined){
let data5 = data.network;
const _errs11 = errors;
if((typeof data5 !== "string") && (data5 !== null)){
validate79.errors = [{instancePath:instancePath+"/network",schemaPath:"#/properties/network/type",keyword:"type",params:{type: schema88.properties.network.type},message:"must be string,null"}];
return false;
}
var valid0 = _errs11 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.output !== undefined){
let data6 = data.output;
const _errs13 = errors;
const _errs14 = errors;
let valid1 = false;
const _errs15 = errors;
if(!(validate80(data6, {instancePath:instancePath+"/output",parentData:data,parentDataProperty:"output",rootData,dynamicAnchors}))){
vErrors = vErrors === null ? validate80.errors : vErrors.concat(validate80.errors);
errors = vErrors.length;
}
var _valid0 = _errs15 === errors;
valid1 = valid1 || _valid0;
const _errs16 = errors;
if(data6 !== null){
const err0 = {instancePath:instancePath+"/output",schemaPath:"#/properties/output/anyOf/1/type",keyword:"type",params:{type: "null"},message:"must be null"};
if(vErrors === null){
vErrors = [err0];
}
else {
vErrors.push(err0);
}
errors++;
}
var _valid0 = _errs16 === errors;
valid1 = valid1 || _valid0;
if(!valid1){
const err1 = {instancePath:instancePath+"/output",schemaPath:"#/properties/output/anyOf",keyword:"anyOf",params:{},message:"must match a schema in anyOf"};
if(vErrors === null){
vErrors = [err1];
}
else {
vErrors.push(err1);
}
errors++;
validate79.errors = vErrors;
return false;
}
else {
errors = _errs14;
if(vErrors !== null){
if(_errs14){
vErrors.length = _errs14;
}
else {
vErrors = null;
}
}
}
var valid0 = _errs13 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.started !== undefined){
let data7 = data.started;
const _errs18 = errors;
if(!(((typeof data7 == "number") && (!(data7 % 1) && !isNaN(data7))) && (isFinite(data7)))){
validate79.errors = [{instancePath:instancePath+"/started",schemaPath:"#/properties/started/type",keyword:"type",params:{type: "integer"},message:"must be integer"}];
return false;
}
if(errors === _errs18){
if((typeof data7 == "number") && (isFinite(data7))){
if(data7 < 0 || isNaN(data7)){
validate79.errors = [{instancePath:instancePath+"/started",schemaPath:"#/properties/started/minimum",keyword:"minimum",params:{comparison: ">=", limit: 0},message:"must be >= 0"}];
return false;
}
}
}
var valid0 = _errs18 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.state !== undefined){
const _errs20 = errors;
if(typeof data.state !== "string"){
validate79.errors = [{instancePath:instancePath+"/state",schemaPath:"#/properties/state/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs20 === errors;
}
else {
var valid0 = true;
}
}
}
}
}
}
}
}
}
}
}
else {
validate79.errors = [{instancePath,schemaPath:"#/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
validate79.errors = vErrors;
return errors === 0;
}
validate79.evaluated = {"props":{"action":true,"conversation":true,"id":true,"instance":true,"message":true,"network":true,"output":true,"started":true,"state":true},"dynamicProps":false,"dynamicItems":false};


function validate76(data, {instancePath="", parentData, parentDataProperty, rootData=data, dynamicAnchors={}}={}){
let vErrors = null;
let errors = 0;
const evaluated0 = validate76.evaluated;
if(evaluated0.dynamicProps){
evaluated0.props = undefined;
}
if(evaluated0.dynamicItems){
evaluated0.items = undefined;
}
if(errors === 0){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing0;
if((((((data.instance === undefined) && (missing0 = "instance")) || ((data.revision === undefined) && (missing0 = "revision"))) || ((data.conversations === undefined) && (missing0 = "conversations"))) || ((data.commandHistory === undefined) && (missing0 = "commandHistory"))) || ((data.inputHistory === undefined) && (missing0 = "inputHistory"))){
validate76.errors = [{instancePath,schemaPath:"#/required",keyword:"required",params:{missingProperty: missing0},message:"must have required property '"+missing0+"'"}];
return false;
}
else {
if(data.activity !== undefined){
let data0 = data.activity;
const _errs1 = errors;
if((!(Array.isArray(data0))) && (data0 !== null)){
validate76.errors = [{instancePath:instancePath+"/activity",schemaPath:"#/properties/activity/type",keyword:"type",params:{type: schema80.properties.activity.type},message:"must be array,null"}];
return false;
}
if(errors === _errs1){
if(Array.isArray(data0)){
var valid1 = true;
const len0 = data0.length;
for(let i0=0; i0<len0; i0++){
let data1 = data0[i0];
const _errs3 = errors;
const _errs4 = errors;
if(errors === _errs4){
if(data1 && typeof data1 == "object" && !Array.isArray(data1)){
let missing1;
if((((((data1.id === undefined) && (missing1 = "id")) || ((data1.conversation === undefined) && (missing1 = "conversation"))) || ((data1.kind === undefined) && (missing1 = "kind"))) || ((data1.text === undefined) && (missing1 = "text"))) || ((data1.timestamp === undefined) && (missing1 = "timestamp"))){
validate76.errors = [{instancePath:instancePath+"/activity/" + i0,schemaPath:"#/$defs/Activity/required",keyword:"required",params:{missingProperty: missing1},message:"must have required property '"+missing1+"'"}];
return false;
}
else {
if(data1.conversation !== undefined){
const _errs6 = errors;
if(typeof data1.conversation !== "string"){
validate76.errors = [{instancePath:instancePath+"/activity/" + i0+"/conversation",schemaPath:"#/$defs/Activity/properties/conversation/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid3 = _errs6 === errors;
}
else {
var valid3 = true;
}
if(valid3){
if(data1.id !== undefined){
const _errs8 = errors;
if(typeof data1.id !== "string"){
validate76.errors = [{instancePath:instancePath+"/activity/" + i0+"/id",schemaPath:"#/$defs/Activity/properties/id/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid3 = _errs8 === errors;
}
else {
var valid3 = true;
}
if(valid3){
if(data1.kind !== undefined){
const _errs10 = errors;
if(typeof data1.kind !== "string"){
validate76.errors = [{instancePath:instancePath+"/activity/" + i0+"/kind",schemaPath:"#/$defs/Activity/properties/kind/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid3 = _errs10 === errors;
}
else {
var valid3 = true;
}
if(valid3){
if(data1.text !== undefined){
const _errs12 = errors;
if(typeof data1.text !== "string"){
validate76.errors = [{instancePath:instancePath+"/activity/" + i0+"/text",schemaPath:"#/$defs/Activity/properties/text/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid3 = _errs12 === errors;
}
else {
var valid3 = true;
}
if(valid3){
if(data1.timestamp !== undefined){
let data6 = data1.timestamp;
const _errs14 = errors;
if(!(((typeof data6 == "number") && (!(data6 % 1) && !isNaN(data6))) && (isFinite(data6)))){
validate76.errors = [{instancePath:instancePath+"/activity/" + i0+"/timestamp",schemaPath:"#/$defs/Activity/properties/timestamp/type",keyword:"type",params:{type: "integer"},message:"must be integer"}];
return false;
}
if(errors === _errs14){
if((typeof data6 == "number") && (isFinite(data6))){
if(data6 < 0 || isNaN(data6)){
validate76.errors = [{instancePath:instancePath+"/activity/" + i0+"/timestamp",schemaPath:"#/$defs/Activity/properties/timestamp/minimum",keyword:"minimum",params:{comparison: ">=", limit: 0},message:"must be >= 0"}];
return false;
}
}
}
var valid3 = _errs14 === errors;
}
else {
var valid3 = true;
}
}
}
}
}
}
}
else {
validate76.errors = [{instancePath:instancePath+"/activity/" + i0,schemaPath:"#/$defs/Activity/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
var valid1 = _errs3 === errors;
if(!valid1){
break;
}
}
}
}
var valid0 = _errs1 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.commandHistory !== undefined){
let data7 = data.commandHistory;
const _errs16 = errors;
if(errors === _errs16){
if(Array.isArray(data7)){
var valid4 = true;
const len1 = data7.length;
for(let i1=0; i1<len1; i1++){
const _errs18 = errors;
if(typeof data7[i1] !== "string"){
validate76.errors = [{instancePath:instancePath+"/commandHistory/" + i1,schemaPath:"#/properties/commandHistory/items/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid4 = _errs18 === errors;
if(!valid4){
break;
}
}
}
else {
validate76.errors = [{instancePath:instancePath+"/commandHistory",schemaPath:"#/properties/commandHistory/type",keyword:"type",params:{type: "array"},message:"must be array"}];
return false;
}
}
var valid0 = _errs16 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.conversations !== undefined){
let data9 = data.conversations;
const _errs20 = errors;
if(errors === _errs20){
if(Array.isArray(data9)){
var valid5 = true;
const len2 = data9.length;
for(let i2=0; i2<len2; i2++){
const _errs22 = errors;
if(!(validate77(data9[i2], {instancePath:instancePath+"/conversations/" + i2,parentData:data9,parentDataProperty:i2,rootData,dynamicAnchors}))){
vErrors = vErrors === null ? validate77.errors : vErrors.concat(validate77.errors);
errors = vErrors.length;
}
var valid5 = _errs22 === errors;
if(!valid5){
break;
}
}
}
else {
validate76.errors = [{instancePath:instancePath+"/conversations",schemaPath:"#/properties/conversations/type",keyword:"type",params:{type: "array"},message:"must be array"}];
return false;
}
}
var valid0 = _errs20 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.inputHistory !== undefined){
let data11 = data.inputHistory;
const _errs23 = errors;
if(errors === _errs23){
if(Array.isArray(data11)){
var valid6 = true;
const len3 = data11.length;
for(let i3=0; i3<len3; i3++){
let data12 = data11[i3];
const _errs25 = errors;
const _errs26 = errors;
if(errors === _errs26){
if(data12 && typeof data12 == "object" && !Array.isArray(data12)){
let missing2;
if((data12.text === undefined) && (missing2 = "text")){
validate76.errors = [{instancePath:instancePath+"/inputHistory/" + i3,schemaPath:"#/$defs/InputHistoryEntry/required",keyword:"required",params:{missingProperty: missing2},message:"must have required property '"+missing2+"'"}];
return false;
}
else {
if(data12.conversation !== undefined){
let data13 = data12.conversation;
const _errs28 = errors;
if((typeof data13 !== "string") && (data13 !== null)){
validate76.errors = [{instancePath:instancePath+"/inputHistory/" + i3+"/conversation",schemaPath:"#/$defs/InputHistoryEntry/properties/conversation/type",keyword:"type",params:{type: schema86.properties.conversation.type},message:"must be string,null"}];
return false;
}
var valid8 = _errs28 === errors;
}
else {
var valid8 = true;
}
if(valid8){
if(data12.text !== undefined){
const _errs30 = errors;
if(typeof data12.text !== "string"){
validate76.errors = [{instancePath:instancePath+"/inputHistory/" + i3+"/text",schemaPath:"#/$defs/InputHistoryEntry/properties/text/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid8 = _errs30 === errors;
}
else {
var valid8 = true;
}
}
}
}
else {
validate76.errors = [{instancePath:instancePath+"/inputHistory/" + i3,schemaPath:"#/$defs/InputHistoryEntry/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
var valid6 = _errs25 === errors;
if(!valid6){
break;
}
}
}
else {
validate76.errors = [{instancePath:instancePath+"/inputHistory",schemaPath:"#/properties/inputHistory/type",keyword:"type",params:{type: "array"},message:"must be array"}];
return false;
}
}
var valid0 = _errs23 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.instance !== undefined){
let data15 = data.instance;
const _errs32 = errors;
const _errs33 = errors;
if(errors === _errs33){
if(data15 && typeof data15 == "object" && !Array.isArray(data15)){
let missing3;
if((((((((((data15.id === undefined) && (missing3 = "id")) || ((data15.label === undefined) && (missing3 = "label"))) || ((data15.bootId === undefined) && (missing3 = "bootId"))) || ((data15.locked === undefined) && (missing3 = "locked"))) || ((data15.protocolLocked === undefined) && (missing3 = "protocolLocked"))) || ((data15.profileExists === undefined) && (missing3 = "profileExists"))) || ((data15.archiveExists === undefined) && (missing3 = "archiveExists"))) || ((data15.safetyNumber === undefined) && (missing3 = "safetyNumber"))) || ((data15.capabilities === undefined) && (missing3 = "capabilities"))){
validate76.errors = [{instancePath:instancePath+"/instance",schemaPath:"#/$defs/InstanceInfo/required",keyword:"required",params:{missingProperty: missing3},message:"must have required property '"+missing3+"'"}];
return false;
}
else {
if(data15.archiveExists !== undefined){
const _errs35 = errors;
if(typeof data15.archiveExists !== "boolean"){
validate76.errors = [{instancePath:instancePath+"/instance/archiveExists",schemaPath:"#/$defs/InstanceInfo/properties/archiveExists/type",keyword:"type",params:{type: "boolean"},message:"must be boolean"}];
return false;
}
var valid10 = _errs35 === errors;
}
else {
var valid10 = true;
}
if(valid10){
if(data15.bootId !== undefined){
const _errs37 = errors;
if(typeof data15.bootId !== "string"){
validate76.errors = [{instancePath:instancePath+"/instance/bootId",schemaPath:"#/$defs/InstanceInfo/properties/bootId/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid10 = _errs37 === errors;
}
else {
var valid10 = true;
}
if(valid10){
if(data15.capabilities !== undefined){
let data18 = data15.capabilities;
const _errs39 = errors;
if(errors === _errs39){
if(Array.isArray(data18)){
var valid11 = true;
const len4 = data18.length;
for(let i4=0; i4<len4; i4++){
const _errs41 = errors;
if(typeof data18[i4] !== "string"){
validate76.errors = [{instancePath:instancePath+"/instance/capabilities/" + i4,schemaPath:"#/$defs/InstanceInfo/properties/capabilities/items/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid11 = _errs41 === errors;
if(!valid11){
break;
}
}
}
else {
validate76.errors = [{instancePath:instancePath+"/instance/capabilities",schemaPath:"#/$defs/InstanceInfo/properties/capabilities/type",keyword:"type",params:{type: "array"},message:"must be array"}];
return false;
}
}
var valid10 = _errs39 === errors;
}
else {
var valid10 = true;
}
if(valid10){
if(data15.id !== undefined){
const _errs43 = errors;
if(typeof data15.id !== "string"){
validate76.errors = [{instancePath:instancePath+"/instance/id",schemaPath:"#/$defs/InstanceInfo/properties/id/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid10 = _errs43 === errors;
}
else {
var valid10 = true;
}
if(valid10){
if(data15.label !== undefined){
const _errs45 = errors;
if(typeof data15.label !== "string"){
validate76.errors = [{instancePath:instancePath+"/instance/label",schemaPath:"#/$defs/InstanceInfo/properties/label/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid10 = _errs45 === errors;
}
else {
var valid10 = true;
}
if(valid10){
if(data15.locked !== undefined){
const _errs47 = errors;
if(typeof data15.locked !== "boolean"){
validate76.errors = [{instancePath:instancePath+"/instance/locked",schemaPath:"#/$defs/InstanceInfo/properties/locked/type",keyword:"type",params:{type: "boolean"},message:"must be boolean"}];
return false;
}
var valid10 = _errs47 === errors;
}
else {
var valid10 = true;
}
if(valid10){
if(data15.profileExists !== undefined){
const _errs49 = errors;
if(typeof data15.profileExists !== "boolean"){
validate76.errors = [{instancePath:instancePath+"/instance/profileExists",schemaPath:"#/$defs/InstanceInfo/properties/profileExists/type",keyword:"type",params:{type: "boolean"},message:"must be boolean"}];
return false;
}
var valid10 = _errs49 === errors;
}
else {
var valid10 = true;
}
if(valid10){
if(data15.protocolLocked !== undefined){
const _errs51 = errors;
if(typeof data15.protocolLocked !== "boolean"){
validate76.errors = [{instancePath:instancePath+"/instance/protocolLocked",schemaPath:"#/$defs/InstanceInfo/properties/protocolLocked/type",keyword:"type",params:{type: "boolean"},message:"must be boolean"}];
return false;
}
var valid10 = _errs51 === errors;
}
else {
var valid10 = true;
}
if(valid10){
if(data15.safetyNumber !== undefined){
const _errs53 = errors;
if(typeof data15.safetyNumber !== "string"){
validate76.errors = [{instancePath:instancePath+"/instance/safetyNumber",schemaPath:"#/$defs/InstanceInfo/properties/safetyNumber/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid10 = _errs53 === errors;
}
else {
var valid10 = true;
}
}
}
}
}
}
}
}
}
}
}
else {
validate76.errors = [{instancePath:instancePath+"/instance",schemaPath:"#/$defs/InstanceInfo/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
var valid0 = _errs32 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.operations !== undefined){
let data26 = data.operations;
const _errs55 = errors;
if((!(Array.isArray(data26))) && (data26 !== null)){
validate76.errors = [{instancePath:instancePath+"/operations",schemaPath:"#/properties/operations/type",keyword:"type",params:{type: schema80.properties.operations.type},message:"must be array,null"}];
return false;
}
if(errors === _errs55){
if(Array.isArray(data26)){
var valid12 = true;
const len5 = data26.length;
for(let i5=0; i5<len5; i5++){
const _errs57 = errors;
if(!(validate79(data26[i5], {instancePath:instancePath+"/operations/" + i5,parentData:data26,parentDataProperty:i5,rootData,dynamicAnchors}))){
vErrors = vErrors === null ? validate79.errors : vErrors.concat(validate79.errors);
errors = vErrors.length;
}
var valid12 = _errs57 === errors;
if(!valid12){
break;
}
}
}
}
var valid0 = _errs55 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.presenceEnabled !== undefined){
let data28 = data.presenceEnabled;
const _errs58 = errors;
if((typeof data28 !== "boolean") && (data28 !== null)){
validate76.errors = [{instancePath:instancePath+"/presenceEnabled",schemaPath:"#/properties/presenceEnabled/type",keyword:"type",params:{type: schema80.properties.presenceEnabled.type},message:"must be boolean,null"}];
return false;
}
var valid0 = _errs58 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.providerErrors !== undefined){
let data29 = data.providerErrors;
const _errs60 = errors;
if(errors === _errs60){
if(Array.isArray(data29)){
var valid13 = true;
const len6 = data29.length;
for(let i6=0; i6<len6; i6++){
let data30 = data29[i6];
const _errs62 = errors;
const _errs63 = errors;
if(errors === _errs63){
if(data30 && typeof data30 == "object" && !Array.isArray(data30)){
let missing4;
if(((((data30.id === undefined) && (missing4 = "id")) || ((data30.code === undefined) && (missing4 = "code"))) || ((data30.message === undefined) && (missing4 = "message"))) || ((data30.retryable === undefined) && (missing4 = "retryable"))){
validate76.errors = [{instancePath:instancePath+"/providerErrors/" + i6,schemaPath:"#/$defs/ProviderStatus/required",keyword:"required",params:{missingProperty: missing4},message:"must have required property '"+missing4+"'"}];
return false;
}
else {
if(data30.code !== undefined){
const _errs65 = errors;
if(typeof data30.code !== "string"){
validate76.errors = [{instancePath:instancePath+"/providerErrors/" + i6+"/code",schemaPath:"#/$defs/ProviderStatus/properties/code/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid15 = _errs65 === errors;
}
else {
var valid15 = true;
}
if(valid15){
if(data30.id !== undefined){
const _errs67 = errors;
if(typeof data30.id !== "string"){
validate76.errors = [{instancePath:instancePath+"/providerErrors/" + i6+"/id",schemaPath:"#/$defs/ProviderStatus/properties/id/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid15 = _errs67 === errors;
}
else {
var valid15 = true;
}
if(valid15){
if(data30.message !== undefined){
const _errs69 = errors;
if(typeof data30.message !== "string"){
validate76.errors = [{instancePath:instancePath+"/providerErrors/" + i6+"/message",schemaPath:"#/$defs/ProviderStatus/properties/message/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid15 = _errs69 === errors;
}
else {
var valid15 = true;
}
if(valid15){
if(data30.retryable !== undefined){
const _errs71 = errors;
if(typeof data30.retryable !== "boolean"){
validate76.errors = [{instancePath:instancePath+"/providerErrors/" + i6+"/retryable",schemaPath:"#/$defs/ProviderStatus/properties/retryable/type",keyword:"type",params:{type: "boolean"},message:"must be boolean"}];
return false;
}
var valid15 = _errs71 === errors;
}
else {
var valid15 = true;
}
}
}
}
}
}
else {
validate76.errors = [{instancePath:instancePath+"/providerErrors/" + i6,schemaPath:"#/$defs/ProviderStatus/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
var valid13 = _errs62 === errors;
if(!valid13){
break;
}
}
}
else {
validate76.errors = [{instancePath:instancePath+"/providerErrors",schemaPath:"#/properties/providerErrors/type",keyword:"type",params:{type: "array"},message:"must be array"}];
return false;
}
}
var valid0 = _errs60 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.revision !== undefined){
const _errs73 = errors;
if(typeof data.revision !== "string"){
validate76.errors = [{instancePath:instancePath+"/revision",schemaPath:"#/properties/revision/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs73 === errors;
}
else {
var valid0 = true;
}
}
}
}
}
}
}
}
}
}
}
else {
validate76.errors = [{instancePath,schemaPath:"#/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
validate76.errors = vErrors;
return errors === 0;
}
validate76.evaluated = {"props":{"activity":true,"commandHistory":true,"conversations":true,"inputHistory":true,"instance":true,"operations":true,"presenceEnabled":true,"providerErrors":true,"revision":true},"dynamicProps":false,"dynamicItems":false};

const schema93 = {"properties":{"before":{"type":["string","null"]},"messages":{"items":{"$ref":"#/$defs/Message"},"type":"array"}},"required":["messages"],"type":"object"};
const schema94 = {"properties":{"body":{"type":"string"},"conversationId":{"type":"string"},"delivery":{"anyOf":[{"$ref":"#/$defs/Delivery"},{"type":"null"}],"description":"Delivered is an authenticated recipient acknowledgement, never a read receipt."},"id":{"type":"string"},"memberId":{"type":["string","null"]},"mine":{"type":"boolean"},"nickname":{"type":"string"},"operationId":{"default":null,"type":["string","null"]},"result":{"anyOf":[{"$ref":"#/$defs/ActionResult"},{"type":"null"}],"default":null},"timestamp":{"format":"uint64","minimum":0,"type":"integer"}},"required":["id","conversationId","nickname","body","timestamp","mine"],"type":"object"};
const schema95 = {"enum":["local_accepted","delivered"],"type":"string"};
const schema96 = {"properties":{"artifacts":{"items":{"$ref":"#/$defs/Artifact"},"type":"array"},"details":{"items":{"type":"string"},"type":"array"},"id":{"type":"string"},"messageId":{"default":null,"type":["string","null"]},"outputBase64":{"description":"Exact signed bytes, base64 encoded; views decode only for display.","type":["string","null"]},"state":{"type":"string"},"stderr":{"type":"boolean"}},"required":["id","state","stderr","details","artifacts"],"type":"object"};
const schema97 = {"properties":{"name":{"type":"string"},"url":{"type":"string"}},"required":["name","url"],"type":"object"};

function validate86(data, {instancePath="", parentData, parentDataProperty, rootData=data, dynamicAnchors={}}={}){
let vErrors = null;
let errors = 0;
const evaluated0 = validate86.evaluated;
if(evaluated0.dynamicProps){
evaluated0.props = undefined;
}
if(evaluated0.dynamicItems){
evaluated0.items = undefined;
}
if(errors === 0){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing0;
if((((((data.id === undefined) && (missing0 = "id")) || ((data.state === undefined) && (missing0 = "state"))) || ((data.stderr === undefined) && (missing0 = "stderr"))) || ((data.details === undefined) && (missing0 = "details"))) || ((data.artifacts === undefined) && (missing0 = "artifacts"))){
validate86.errors = [{instancePath,schemaPath:"#/required",keyword:"required",params:{missingProperty: missing0},message:"must have required property '"+missing0+"'"}];
return false;
}
else {
if(data.artifacts !== undefined){
let data0 = data.artifacts;
const _errs1 = errors;
if(errors === _errs1){
if(Array.isArray(data0)){
var valid1 = true;
const len0 = data0.length;
for(let i0=0; i0<len0; i0++){
let data1 = data0[i0];
const _errs3 = errors;
const _errs4 = errors;
if(errors === _errs4){
if(data1 && typeof data1 == "object" && !Array.isArray(data1)){
let missing1;
if(((data1.name === undefined) && (missing1 = "name")) || ((data1.url === undefined) && (missing1 = "url"))){
validate86.errors = [{instancePath:instancePath+"/artifacts/" + i0,schemaPath:"#/$defs/Artifact/required",keyword:"required",params:{missingProperty: missing1},message:"must have required property '"+missing1+"'"}];
return false;
}
else {
if(data1.name !== undefined){
const _errs6 = errors;
if(typeof data1.name !== "string"){
validate86.errors = [{instancePath:instancePath+"/artifacts/" + i0+"/name",schemaPath:"#/$defs/Artifact/properties/name/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid3 = _errs6 === errors;
}
else {
var valid3 = true;
}
if(valid3){
if(data1.url !== undefined){
const _errs8 = errors;
if(typeof data1.url !== "string"){
validate86.errors = [{instancePath:instancePath+"/artifacts/" + i0+"/url",schemaPath:"#/$defs/Artifact/properties/url/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid3 = _errs8 === errors;
}
else {
var valid3 = true;
}
}
}
}
else {
validate86.errors = [{instancePath:instancePath+"/artifacts/" + i0,schemaPath:"#/$defs/Artifact/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
var valid1 = _errs3 === errors;
if(!valid1){
break;
}
}
}
else {
validate86.errors = [{instancePath:instancePath+"/artifacts",schemaPath:"#/properties/artifacts/type",keyword:"type",params:{type: "array"},message:"must be array"}];
return false;
}
}
var valid0 = _errs1 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.details !== undefined){
let data4 = data.details;
const _errs10 = errors;
if(errors === _errs10){
if(Array.isArray(data4)){
var valid4 = true;
const len1 = data4.length;
for(let i1=0; i1<len1; i1++){
const _errs12 = errors;
if(typeof data4[i1] !== "string"){
validate86.errors = [{instancePath:instancePath+"/details/" + i1,schemaPath:"#/properties/details/items/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid4 = _errs12 === errors;
if(!valid4){
break;
}
}
}
else {
validate86.errors = [{instancePath:instancePath+"/details",schemaPath:"#/properties/details/type",keyword:"type",params:{type: "array"},message:"must be array"}];
return false;
}
}
var valid0 = _errs10 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.id !== undefined){
const _errs14 = errors;
if(typeof data.id !== "string"){
validate86.errors = [{instancePath:instancePath+"/id",schemaPath:"#/properties/id/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs14 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.messageId !== undefined){
let data7 = data.messageId;
const _errs16 = errors;
if((typeof data7 !== "string") && (data7 !== null)){
validate86.errors = [{instancePath:instancePath+"/messageId",schemaPath:"#/properties/messageId/type",keyword:"type",params:{type: schema96.properties.messageId.type},message:"must be string,null"}];
return false;
}
var valid0 = _errs16 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.outputBase64 !== undefined){
let data8 = data.outputBase64;
const _errs18 = errors;
if((typeof data8 !== "string") && (data8 !== null)){
validate86.errors = [{instancePath:instancePath+"/outputBase64",schemaPath:"#/properties/outputBase64/type",keyword:"type",params:{type: schema96.properties.outputBase64.type},message:"must be string,null"}];
return false;
}
var valid0 = _errs18 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.state !== undefined){
const _errs20 = errors;
if(typeof data.state !== "string"){
validate86.errors = [{instancePath:instancePath+"/state",schemaPath:"#/properties/state/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs20 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.stderr !== undefined){
const _errs22 = errors;
if(typeof data.stderr !== "boolean"){
validate86.errors = [{instancePath:instancePath+"/stderr",schemaPath:"#/properties/stderr/type",keyword:"type",params:{type: "boolean"},message:"must be boolean"}];
return false;
}
var valid0 = _errs22 === errors;
}
else {
var valid0 = true;
}
}
}
}
}
}
}
}
}
else {
validate86.errors = [{instancePath,schemaPath:"#/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
validate86.errors = vErrors;
return errors === 0;
}
validate86.evaluated = {"props":{"artifacts":true,"details":true,"id":true,"messageId":true,"outputBase64":true,"state":true,"stderr":true},"dynamicProps":false,"dynamicItems":false};


function validate85(data, {instancePath="", parentData, parentDataProperty, rootData=data, dynamicAnchors={}}={}){
let vErrors = null;
let errors = 0;
const evaluated0 = validate85.evaluated;
if(evaluated0.dynamicProps){
evaluated0.props = undefined;
}
if(evaluated0.dynamicItems){
evaluated0.items = undefined;
}
if(errors === 0){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing0;
if(((((((data.id === undefined) && (missing0 = "id")) || ((data.conversationId === undefined) && (missing0 = "conversationId"))) || ((data.nickname === undefined) && (missing0 = "nickname"))) || ((data.body === undefined) && (missing0 = "body"))) || ((data.timestamp === undefined) && (missing0 = "timestamp"))) || ((data.mine === undefined) && (missing0 = "mine"))){
validate85.errors = [{instancePath,schemaPath:"#/required",keyword:"required",params:{missingProperty: missing0},message:"must have required property '"+missing0+"'"}];
return false;
}
else {
if(data.body !== undefined){
const _errs1 = errors;
if(typeof data.body !== "string"){
validate85.errors = [{instancePath:instancePath+"/body",schemaPath:"#/properties/body/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs1 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.conversationId !== undefined){
const _errs3 = errors;
if(typeof data.conversationId !== "string"){
validate85.errors = [{instancePath:instancePath+"/conversationId",schemaPath:"#/properties/conversationId/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs3 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.delivery !== undefined){
let data2 = data.delivery;
const _errs5 = errors;
const _errs6 = errors;
let valid1 = false;
const _errs7 = errors;
if(typeof data2 !== "string"){
const err0 = {instancePath:instancePath+"/delivery",schemaPath:"#/$defs/Delivery/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err0];
}
else {
vErrors.push(err0);
}
errors++;
}
if(!((data2 === "local_accepted") || (data2 === "delivered"))){
const err1 = {instancePath:instancePath+"/delivery",schemaPath:"#/$defs/Delivery/enum",keyword:"enum",params:{allowedValues: schema95.enum},message:"must be equal to one of the allowed values"};
if(vErrors === null){
vErrors = [err1];
}
else {
vErrors.push(err1);
}
errors++;
}
var _valid0 = _errs7 === errors;
valid1 = valid1 || _valid0;
const _errs10 = errors;
if(data2 !== null){
const err2 = {instancePath:instancePath+"/delivery",schemaPath:"#/properties/delivery/anyOf/1/type",keyword:"type",params:{type: "null"},message:"must be null"};
if(vErrors === null){
vErrors = [err2];
}
else {
vErrors.push(err2);
}
errors++;
}
var _valid0 = _errs10 === errors;
valid1 = valid1 || _valid0;
if(!valid1){
const err3 = {instancePath:instancePath+"/delivery",schemaPath:"#/properties/delivery/anyOf",keyword:"anyOf",params:{},message:"must match a schema in anyOf"};
if(vErrors === null){
vErrors = [err3];
}
else {
vErrors.push(err3);
}
errors++;
validate85.errors = vErrors;
return false;
}
else {
errors = _errs6;
if(vErrors !== null){
if(_errs6){
vErrors.length = _errs6;
}
else {
vErrors = null;
}
}
}
var valid0 = _errs5 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.id !== undefined){
const _errs12 = errors;
if(typeof data.id !== "string"){
validate85.errors = [{instancePath:instancePath+"/id",schemaPath:"#/properties/id/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs12 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.memberId !== undefined){
let data4 = data.memberId;
const _errs14 = errors;
if((typeof data4 !== "string") && (data4 !== null)){
validate85.errors = [{instancePath:instancePath+"/memberId",schemaPath:"#/properties/memberId/type",keyword:"type",params:{type: schema94.properties.memberId.type},message:"must be string,null"}];
return false;
}
var valid0 = _errs14 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.mine !== undefined){
const _errs16 = errors;
if(typeof data.mine !== "boolean"){
validate85.errors = [{instancePath:instancePath+"/mine",schemaPath:"#/properties/mine/type",keyword:"type",params:{type: "boolean"},message:"must be boolean"}];
return false;
}
var valid0 = _errs16 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.nickname !== undefined){
const _errs18 = errors;
if(typeof data.nickname !== "string"){
validate85.errors = [{instancePath:instancePath+"/nickname",schemaPath:"#/properties/nickname/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs18 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.operationId !== undefined){
let data7 = data.operationId;
const _errs20 = errors;
if((typeof data7 !== "string") && (data7 !== null)){
validate85.errors = [{instancePath:instancePath+"/operationId",schemaPath:"#/properties/operationId/type",keyword:"type",params:{type: schema94.properties.operationId.type},message:"must be string,null"}];
return false;
}
var valid0 = _errs20 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.result !== undefined){
let data8 = data.result;
const _errs22 = errors;
const _errs23 = errors;
let valid3 = false;
const _errs24 = errors;
if(!(validate86(data8, {instancePath:instancePath+"/result",parentData:data,parentDataProperty:"result",rootData,dynamicAnchors}))){
vErrors = vErrors === null ? validate86.errors : vErrors.concat(validate86.errors);
errors = vErrors.length;
}
var _valid1 = _errs24 === errors;
valid3 = valid3 || _valid1;
if(_valid1){
var props0 = {};
props0.artifacts = true;
props0.details = true;
props0.id = true;
props0.messageId = true;
props0.outputBase64 = true;
props0.state = true;
props0.stderr = true;
}
const _errs25 = errors;
if(data8 !== null){
const err4 = {instancePath:instancePath+"/result",schemaPath:"#/properties/result/anyOf/1/type",keyword:"type",params:{type: "null"},message:"must be null"};
if(vErrors === null){
vErrors = [err4];
}
else {
vErrors.push(err4);
}
errors++;
}
var _valid1 = _errs25 === errors;
valid3 = valid3 || _valid1;
if(!valid3){
const err5 = {instancePath:instancePath+"/result",schemaPath:"#/properties/result/anyOf",keyword:"anyOf",params:{},message:"must match a schema in anyOf"};
if(vErrors === null){
vErrors = [err5];
}
else {
vErrors.push(err5);
}
errors++;
validate85.errors = vErrors;
return false;
}
else {
errors = _errs23;
if(vErrors !== null){
if(_errs23){
vErrors.length = _errs23;
}
else {
vErrors = null;
}
}
}
var valid0 = _errs22 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.timestamp !== undefined){
let data9 = data.timestamp;
const _errs27 = errors;
if(!(((typeof data9 == "number") && (!(data9 % 1) && !isNaN(data9))) && (isFinite(data9)))){
validate85.errors = [{instancePath:instancePath+"/timestamp",schemaPath:"#/properties/timestamp/type",keyword:"type",params:{type: "integer"},message:"must be integer"}];
return false;
}
if(errors === _errs27){
if((typeof data9 == "number") && (isFinite(data9))){
if(data9 < 0 || isNaN(data9)){
validate85.errors = [{instancePath:instancePath+"/timestamp",schemaPath:"#/properties/timestamp/minimum",keyword:"minimum",params:{comparison: ">=", limit: 0},message:"must be >= 0"}];
return false;
}
}
}
var valid0 = _errs27 === errors;
}
else {
var valid0 = true;
}
}
}
}
}
}
}
}
}
}
}
}
else {
validate85.errors = [{instancePath,schemaPath:"#/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
validate85.errors = vErrors;
return errors === 0;
}
validate85.evaluated = {"props":{"body":true,"conversationId":true,"delivery":true,"id":true,"memberId":true,"mine":true,"nickname":true,"operationId":true,"result":true,"timestamp":true},"dynamicProps":false,"dynamicItems":false};


function validate84(data, {instancePath="", parentData, parentDataProperty, rootData=data, dynamicAnchors={}}={}){
let vErrors = null;
let errors = 0;
const evaluated0 = validate84.evaluated;
if(evaluated0.dynamicProps){
evaluated0.props = undefined;
}
if(evaluated0.dynamicItems){
evaluated0.items = undefined;
}
if(errors === 0){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing0;
if((data.messages === undefined) && (missing0 = "messages")){
validate84.errors = [{instancePath,schemaPath:"#/required",keyword:"required",params:{missingProperty: missing0},message:"must have required property '"+missing0+"'"}];
return false;
}
else {
if(data.before !== undefined){
let data0 = data.before;
const _errs1 = errors;
if((typeof data0 !== "string") && (data0 !== null)){
validate84.errors = [{instancePath:instancePath+"/before",schemaPath:"#/properties/before/type",keyword:"type",params:{type: schema93.properties.before.type},message:"must be string,null"}];
return false;
}
var valid0 = _errs1 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.messages !== undefined){
let data1 = data.messages;
const _errs3 = errors;
if(errors === _errs3){
if(Array.isArray(data1)){
var valid1 = true;
const len0 = data1.length;
for(let i0=0; i0<len0; i0++){
const _errs5 = errors;
if(!(validate85(data1[i0], {instancePath:instancePath+"/messages/" + i0,parentData:data1,parentDataProperty:i0,rootData,dynamicAnchors}))){
vErrors = vErrors === null ? validate85.errors : vErrors.concat(validate85.errors);
errors = vErrors.length;
}
var valid1 = _errs5 === errors;
if(!valid1){
break;
}
}
}
else {
validate84.errors = [{instancePath:instancePath+"/messages",schemaPath:"#/properties/messages/type",keyword:"type",params:{type: "array"},message:"must be array"}];
return false;
}
}
var valid0 = _errs3 === errors;
}
else {
var valid0 = true;
}
}
}
}
else {
validate84.errors = [{instancePath,schemaPath:"#/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
validate84.errors = vErrors;
return errors === 0;
}
validate84.evaluated = {"props":{"before":true,"messages":true},"dynamicProps":false,"dynamicItems":false};


function validate70(data, {instancePath="", parentData, parentDataProperty, rootData=data, dynamicAnchors={}}={}){
let vErrors = null;
let errors = 0;
const evaluated0 = validate70.evaluated;
if(evaluated0.dynamicProps){
evaluated0.props = undefined;
}
if(evaluated0.dynamicItems){
evaluated0.items = undefined;
}
const _errs0 = errors;
let valid0 = false;
let passing0 = null;
const _errs1 = errors;
if(errors === _errs1){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing0;
if(((data.kind === undefined) && (missing0 = "kind")) || ((data.response === undefined) && (missing0 = "response"))){
const err0 = {instancePath,schemaPath:"#/oneOf/0/required",keyword:"required",params:{missingProperty: missing0},message:"must have required property '"+missing0+"'"};
if(vErrors === null){
vErrors = [err0];
}
else {
vErrors.push(err0);
}
errors++;
}
else {
if(data.kind !== undefined){
let data0 = data.kind;
const _errs3 = errors;
if(typeof data0 !== "string"){
const err1 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/0/properties/kind/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err1];
}
else {
vErrors.push(err1);
}
errors++;
}
if("networks" !== data0){
const err2 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/0/properties/kind/const",keyword:"const",params:{allowedValue: "networks"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err2];
}
else {
vErrors.push(err2);
}
errors++;
}
var valid1 = _errs3 === errors;
}
else {
var valid1 = true;
}
if(valid1){
if(data.response !== undefined){
const _errs5 = errors;
if(!(root1.validate(data.response, {instancePath:instancePath+"/response",parentData:data,parentDataProperty:"response",rootData,dynamicAnchors}))){
vErrors = vErrors === null ? root1.validate.errors : vErrors.concat(root1.validate.errors);
errors = vErrors.length;
}
var valid1 = _errs5 === errors;
}
else {
var valid1 = true;
}
}
}
}
else {
const err3 = {instancePath,schemaPath:"#/oneOf/0/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err3];
}
else {
vErrors.push(err3);
}
errors++;
}
}
var _valid0 = _errs1 === errors;
if(_valid0){
valid0 = true;
passing0 = 0;
var props1 = {};
props1.kind = true;
props1.response = true;
}
const _errs6 = errors;
if(errors === _errs6){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing1;
if(((data.kind === undefined) && (missing1 = "kind")) || ((data.snapshot === undefined) && (missing1 = "snapshot"))){
const err4 = {instancePath,schemaPath:"#/oneOf/1/required",keyword:"required",params:{missingProperty: missing1},message:"must have required property '"+missing1+"'"};
if(vErrors === null){
vErrors = [err4];
}
else {
vErrors.push(err4);
}
errors++;
}
else {
if(data.kind !== undefined){
let data2 = data.kind;
const _errs8 = errors;
if(typeof data2 !== "string"){
const err5 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/1/properties/kind/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err5];
}
else {
vErrors.push(err5);
}
errors++;
}
if("files" !== data2){
const err6 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/1/properties/kind/const",keyword:"const",params:{allowedValue: "files"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err6];
}
else {
vErrors.push(err6);
}
errors++;
}
var valid2 = _errs8 === errors;
}
else {
var valid2 = true;
}
if(valid2){
if(data.snapshot !== undefined){
const _errs10 = errors;
if(!(validate71(data.snapshot, {instancePath:instancePath+"/snapshot",parentData:data,parentDataProperty:"snapshot",rootData,dynamicAnchors}))){
vErrors = vErrors === null ? validate71.errors : vErrors.concat(validate71.errors);
errors = vErrors.length;
}
var valid2 = _errs10 === errors;
}
else {
var valid2 = true;
}
}
}
}
else {
const err7 = {instancePath,schemaPath:"#/oneOf/1/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err7];
}
else {
vErrors.push(err7);
}
errors++;
}
}
var _valid0 = _errs6 === errors;
if(_valid0 && valid0){
valid0 = false;
passing0 = [passing0, 1];
}
else {
if(_valid0){
valid0 = true;
passing0 = 1;
if(props1 !== true){
props1 = props1 || {};
props1.kind = true;
props1.snapshot = true;
}
}
const _errs11 = errors;
if(errors === _errs11){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing2;
if(((data.kind === undefined) && (missing2 = "kind")) || ((data.status === undefined) && (missing2 = "status"))){
const err8 = {instancePath,schemaPath:"#/oneOf/2/required",keyword:"required",params:{missingProperty: missing2},message:"must have required property '"+missing2+"'"};
if(vErrors === null){
vErrors = [err8];
}
else {
vErrors.push(err8);
}
errors++;
}
else {
if(data.kind !== undefined){
let data4 = data.kind;
const _errs13 = errors;
if(typeof data4 !== "string"){
const err9 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/2/properties/kind/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err9];
}
else {
vErrors.push(err9);
}
errors++;
}
if("network_status" !== data4){
const err10 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/2/properties/kind/const",keyword:"const",params:{allowedValue: "network_status"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err10];
}
else {
vErrors.push(err10);
}
errors++;
}
var valid3 = _errs13 === errors;
}
else {
var valid3 = true;
}
if(valid3){
if(data.status !== undefined){
const _errs15 = errors;
if(!(validate64(data.status, {instancePath:instancePath+"/status",parentData:data,parentDataProperty:"status",rootData,dynamicAnchors}))){
vErrors = vErrors === null ? validate64.errors : vErrors.concat(validate64.errors);
errors = vErrors.length;
}
var valid3 = _errs15 === errors;
}
else {
var valid3 = true;
}
}
}
}
else {
const err11 = {instancePath,schemaPath:"#/oneOf/2/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err11];
}
else {
vErrors.push(err11);
}
errors++;
}
}
var _valid0 = _errs11 === errors;
if(_valid0 && valid0){
valid0 = false;
passing0 = [passing0, 2];
}
else {
if(_valid0){
valid0 = true;
passing0 = 2;
if(props1 !== true){
props1 = props1 || {};
props1.kind = true;
props1.status = true;
}
}
const _errs16 = errors;
if(errors === _errs16){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing3;
if(((data.kind === undefined) && (missing3 = "kind")) || ((data.instance === undefined) && (missing3 = "instance"))){
const err12 = {instancePath,schemaPath:"#/oneOf/3/required",keyword:"required",params:{missingProperty: missing3},message:"must have required property '"+missing3+"'"};
if(vErrors === null){
vErrors = [err12];
}
else {
vErrors.push(err12);
}
errors++;
}
else {
if(data.instance !== undefined){
let data6 = data.instance;
const _errs18 = errors;
const _errs19 = errors;
if(errors === _errs19){
if(data6 && typeof data6 == "object" && !Array.isArray(data6)){
let missing4;
if((((((((((data6.id === undefined) && (missing4 = "id")) || ((data6.label === undefined) && (missing4 = "label"))) || ((data6.bootId === undefined) && (missing4 = "bootId"))) || ((data6.locked === undefined) && (missing4 = "locked"))) || ((data6.protocolLocked === undefined) && (missing4 = "protocolLocked"))) || ((data6.profileExists === undefined) && (missing4 = "profileExists"))) || ((data6.archiveExists === undefined) && (missing4 = "archiveExists"))) || ((data6.safetyNumber === undefined) && (missing4 = "safetyNumber"))) || ((data6.capabilities === undefined) && (missing4 = "capabilities"))){
const err13 = {instancePath:instancePath+"/instance",schemaPath:"#/$defs/InstanceInfo/required",keyword:"required",params:{missingProperty: missing4},message:"must have required property '"+missing4+"'"};
if(vErrors === null){
vErrors = [err13];
}
else {
vErrors.push(err13);
}
errors++;
}
else {
if(data6.archiveExists !== undefined){
const _errs21 = errors;
if(typeof data6.archiveExists !== "boolean"){
const err14 = {instancePath:instancePath+"/instance/archiveExists",schemaPath:"#/$defs/InstanceInfo/properties/archiveExists/type",keyword:"type",params:{type: "boolean"},message:"must be boolean"};
if(vErrors === null){
vErrors = [err14];
}
else {
vErrors.push(err14);
}
errors++;
}
var valid6 = _errs21 === errors;
}
else {
var valid6 = true;
}
if(valid6){
if(data6.bootId !== undefined){
const _errs23 = errors;
if(typeof data6.bootId !== "string"){
const err15 = {instancePath:instancePath+"/instance/bootId",schemaPath:"#/$defs/InstanceInfo/properties/bootId/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err15];
}
else {
vErrors.push(err15);
}
errors++;
}
var valid6 = _errs23 === errors;
}
else {
var valid6 = true;
}
if(valid6){
if(data6.capabilities !== undefined){
let data9 = data6.capabilities;
const _errs25 = errors;
if(errors === _errs25){
if(Array.isArray(data9)){
var valid7 = true;
const len0 = data9.length;
for(let i0=0; i0<len0; i0++){
const _errs27 = errors;
if(typeof data9[i0] !== "string"){
const err16 = {instancePath:instancePath+"/instance/capabilities/" + i0,schemaPath:"#/$defs/InstanceInfo/properties/capabilities/items/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err16];
}
else {
vErrors.push(err16);
}
errors++;
}
var valid7 = _errs27 === errors;
if(!valid7){
break;
}
}
}
else {
const err17 = {instancePath:instancePath+"/instance/capabilities",schemaPath:"#/$defs/InstanceInfo/properties/capabilities/type",keyword:"type",params:{type: "array"},message:"must be array"};
if(vErrors === null){
vErrors = [err17];
}
else {
vErrors.push(err17);
}
errors++;
}
}
var valid6 = _errs25 === errors;
}
else {
var valid6 = true;
}
if(valid6){
if(data6.id !== undefined){
const _errs29 = errors;
if(typeof data6.id !== "string"){
const err18 = {instancePath:instancePath+"/instance/id",schemaPath:"#/$defs/InstanceInfo/properties/id/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err18];
}
else {
vErrors.push(err18);
}
errors++;
}
var valid6 = _errs29 === errors;
}
else {
var valid6 = true;
}
if(valid6){
if(data6.label !== undefined){
const _errs31 = errors;
if(typeof data6.label !== "string"){
const err19 = {instancePath:instancePath+"/instance/label",schemaPath:"#/$defs/InstanceInfo/properties/label/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err19];
}
else {
vErrors.push(err19);
}
errors++;
}
var valid6 = _errs31 === errors;
}
else {
var valid6 = true;
}
if(valid6){
if(data6.locked !== undefined){
const _errs33 = errors;
if(typeof data6.locked !== "boolean"){
const err20 = {instancePath:instancePath+"/instance/locked",schemaPath:"#/$defs/InstanceInfo/properties/locked/type",keyword:"type",params:{type: "boolean"},message:"must be boolean"};
if(vErrors === null){
vErrors = [err20];
}
else {
vErrors.push(err20);
}
errors++;
}
var valid6 = _errs33 === errors;
}
else {
var valid6 = true;
}
if(valid6){
if(data6.profileExists !== undefined){
const _errs35 = errors;
if(typeof data6.profileExists !== "boolean"){
const err21 = {instancePath:instancePath+"/instance/profileExists",schemaPath:"#/$defs/InstanceInfo/properties/profileExists/type",keyword:"type",params:{type: "boolean"},message:"must be boolean"};
if(vErrors === null){
vErrors = [err21];
}
else {
vErrors.push(err21);
}
errors++;
}
var valid6 = _errs35 === errors;
}
else {
var valid6 = true;
}
if(valid6){
if(data6.protocolLocked !== undefined){
const _errs37 = errors;
if(typeof data6.protocolLocked !== "boolean"){
const err22 = {instancePath:instancePath+"/instance/protocolLocked",schemaPath:"#/$defs/InstanceInfo/properties/protocolLocked/type",keyword:"type",params:{type: "boolean"},message:"must be boolean"};
if(vErrors === null){
vErrors = [err22];
}
else {
vErrors.push(err22);
}
errors++;
}
var valid6 = _errs37 === errors;
}
else {
var valid6 = true;
}
if(valid6){
if(data6.safetyNumber !== undefined){
const _errs39 = errors;
if(typeof data6.safetyNumber !== "string"){
const err23 = {instancePath:instancePath+"/instance/safetyNumber",schemaPath:"#/$defs/InstanceInfo/properties/safetyNumber/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err23];
}
else {
vErrors.push(err23);
}
errors++;
}
var valid6 = _errs39 === errors;
}
else {
var valid6 = true;
}
}
}
}
}
}
}
}
}
}
}
else {
const err24 = {instancePath:instancePath+"/instance",schemaPath:"#/$defs/InstanceInfo/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err24];
}
else {
vErrors.push(err24);
}
errors++;
}
}
var valid4 = _errs18 === errors;
}
else {
var valid4 = true;
}
if(valid4){
if(data.kind !== undefined){
let data17 = data.kind;
const _errs41 = errors;
if(typeof data17 !== "string"){
const err25 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/3/properties/kind/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err25];
}
else {
vErrors.push(err25);
}
errors++;
}
if("instance" !== data17){
const err26 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/3/properties/kind/const",keyword:"const",params:{allowedValue: "instance"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err26];
}
else {
vErrors.push(err26);
}
errors++;
}
var valid4 = _errs41 === errors;
}
else {
var valid4 = true;
}
}
}
}
else {
const err27 = {instancePath,schemaPath:"#/oneOf/3/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err27];
}
else {
vErrors.push(err27);
}
errors++;
}
}
var _valid0 = _errs16 === errors;
if(_valid0 && valid0){
valid0 = false;
passing0 = [passing0, 3];
}
else {
if(_valid0){
valid0 = true;
passing0 = 3;
if(props1 !== true){
props1 = props1 || {};
props1.instance = true;
props1.kind = true;
}
}
const _errs43 = errors;
if(errors === _errs43){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing5;
if(((data.kind === undefined) && (missing5 = "kind")) || ((data.snapshot === undefined) && (missing5 = "snapshot"))){
const err28 = {instancePath,schemaPath:"#/oneOf/4/required",keyword:"required",params:{missingProperty: missing5},message:"must have required property '"+missing5+"'"};
if(vErrors === null){
vErrors = [err28];
}
else {
vErrors.push(err28);
}
errors++;
}
else {
if(data.kind !== undefined){
let data18 = data.kind;
const _errs45 = errors;
if(typeof data18 !== "string"){
const err29 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/4/properties/kind/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err29];
}
else {
vErrors.push(err29);
}
errors++;
}
if("snapshot" !== data18){
const err30 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/4/properties/kind/const",keyword:"const",params:{allowedValue: "snapshot"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err30];
}
else {
vErrors.push(err30);
}
errors++;
}
var valid8 = _errs45 === errors;
}
else {
var valid8 = true;
}
if(valid8){
if(data.snapshot !== undefined){
const _errs47 = errors;
if(!(validate76(data.snapshot, {instancePath:instancePath+"/snapshot",parentData:data,parentDataProperty:"snapshot",rootData,dynamicAnchors}))){
vErrors = vErrors === null ? validate76.errors : vErrors.concat(validate76.errors);
errors = vErrors.length;
}
var valid8 = _errs47 === errors;
}
else {
var valid8 = true;
}
}
}
}
else {
const err31 = {instancePath,schemaPath:"#/oneOf/4/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err31];
}
else {
vErrors.push(err31);
}
errors++;
}
}
var _valid0 = _errs43 === errors;
if(_valid0 && valid0){
valid0 = false;
passing0 = [passing0, 4];
}
else {
if(_valid0){
valid0 = true;
passing0 = 4;
if(props1 !== true){
props1 = props1 || {};
props1.kind = true;
props1.snapshot = true;
}
}
const _errs48 = errors;
if(errors === _errs48){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing6;
if(((data.kind === undefined) && (missing6 = "kind")) || ((data.page === undefined) && (missing6 = "page"))){
const err32 = {instancePath,schemaPath:"#/oneOf/5/required",keyword:"required",params:{missingProperty: missing6},message:"must have required property '"+missing6+"'"};
if(vErrors === null){
vErrors = [err32];
}
else {
vErrors.push(err32);
}
errors++;
}
else {
if(data.kind !== undefined){
let data20 = data.kind;
const _errs50 = errors;
if(typeof data20 !== "string"){
const err33 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/5/properties/kind/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err33];
}
else {
vErrors.push(err33);
}
errors++;
}
if("history" !== data20){
const err34 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/5/properties/kind/const",keyword:"const",params:{allowedValue: "history"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err34];
}
else {
vErrors.push(err34);
}
errors++;
}
var valid9 = _errs50 === errors;
}
else {
var valid9 = true;
}
if(valid9){
if(data.page !== undefined){
const _errs52 = errors;
if(!(validate84(data.page, {instancePath:instancePath+"/page",parentData:data,parentDataProperty:"page",rootData,dynamicAnchors}))){
vErrors = vErrors === null ? validate84.errors : vErrors.concat(validate84.errors);
errors = vErrors.length;
}
var valid9 = _errs52 === errors;
}
else {
var valid9 = true;
}
}
}
}
else {
const err35 = {instancePath,schemaPath:"#/oneOf/5/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err35];
}
else {
vErrors.push(err35);
}
errors++;
}
}
var _valid0 = _errs48 === errors;
if(_valid0 && valid0){
valid0 = false;
passing0 = [passing0, 5];
}
else {
if(_valid0){
valid0 = true;
passing0 = 5;
if(props1 !== true){
props1 = props1 || {};
props1.kind = true;
props1.page = true;
}
}
const _errs53 = errors;
if(errors === _errs53){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing7;
if(((data.kind === undefined) && (missing7 = "kind")) || ((data.items === undefined) && (missing7 = "items"))){
const err36 = {instancePath,schemaPath:"#/oneOf/6/required",keyword:"required",params:{missingProperty: missing7},message:"must have required property '"+missing7+"'"};
if(vErrors === null){
vErrors = [err36];
}
else {
vErrors.push(err36);
}
errors++;
}
else {
if(data.items !== undefined){
let data22 = data.items;
const _errs55 = errors;
if(errors === _errs55){
if(Array.isArray(data22)){
var valid11 = true;
const len1 = data22.length;
for(let i1=0; i1<len1; i1++){
let data23 = data22[i1];
const _errs57 = errors;
const _errs58 = errors;
if(errors === _errs58){
if(data23 && typeof data23 == "object" && !Array.isArray(data23)){
let missing8;
if(((data23.text === undefined) && (missing8 = "text")) || ((data23.description === undefined) && (missing8 = "description"))){
const err37 = {instancePath:instancePath+"/items/" + i1,schemaPath:"#/$defs/Completion/required",keyword:"required",params:{missingProperty: missing8},message:"must have required property '"+missing8+"'"};
if(vErrors === null){
vErrors = [err37];
}
else {
vErrors.push(err37);
}
errors++;
}
else {
if(data23.description !== undefined){
const _errs60 = errors;
if(typeof data23.description !== "string"){
const err38 = {instancePath:instancePath+"/items/" + i1+"/description",schemaPath:"#/$defs/Completion/properties/description/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err38];
}
else {
vErrors.push(err38);
}
errors++;
}
var valid13 = _errs60 === errors;
}
else {
var valid13 = true;
}
if(valid13){
if(data23.text !== undefined){
const _errs62 = errors;
if(typeof data23.text !== "string"){
const err39 = {instancePath:instancePath+"/items/" + i1+"/text",schemaPath:"#/$defs/Completion/properties/text/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err39];
}
else {
vErrors.push(err39);
}
errors++;
}
var valid13 = _errs62 === errors;
}
else {
var valid13 = true;
}
}
}
}
else {
const err40 = {instancePath:instancePath+"/items/" + i1,schemaPath:"#/$defs/Completion/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err40];
}
else {
vErrors.push(err40);
}
errors++;
}
}
var valid11 = _errs57 === errors;
if(!valid11){
break;
}
}
}
else {
const err41 = {instancePath:instancePath+"/items",schemaPath:"#/oneOf/6/properties/items/type",keyword:"type",params:{type: "array"},message:"must be array"};
if(vErrors === null){
vErrors = [err41];
}
else {
vErrors.push(err41);
}
errors++;
}
}
var valid10 = _errs55 === errors;
}
else {
var valid10 = true;
}
if(valid10){
if(data.kind !== undefined){
let data26 = data.kind;
const _errs64 = errors;
if(typeof data26 !== "string"){
const err42 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/6/properties/kind/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err42];
}
else {
vErrors.push(err42);
}
errors++;
}
if("completed" !== data26){
const err43 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/6/properties/kind/const",keyword:"const",params:{allowedValue: "completed"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err43];
}
else {
vErrors.push(err43);
}
errors++;
}
var valid10 = _errs64 === errors;
}
else {
var valid10 = true;
}
}
}
}
else {
const err44 = {instancePath,schemaPath:"#/oneOf/6/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err44];
}
else {
vErrors.push(err44);
}
errors++;
}
}
var _valid0 = _errs53 === errors;
if(_valid0 && valid0){
valid0 = false;
passing0 = [passing0, 6];
}
else {
if(_valid0){
valid0 = true;
passing0 = 6;
if(props1 !== true){
props1 = props1 || {};
props1.items = true;
props1.kind = true;
}
}
const _errs66 = errors;
if(errors === _errs66){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing9;
if(((data.kind === undefined) && (missing9 = "kind")) || ((data.commands === undefined) && (missing9 = "commands"))){
const err45 = {instancePath,schemaPath:"#/oneOf/7/required",keyword:"required",params:{missingProperty: missing9},message:"must have required property '"+missing9+"'"};
if(vErrors === null){
vErrors = [err45];
}
else {
vErrors.push(err45);
}
errors++;
}
else {
if(data.commands !== undefined){
let data27 = data.commands;
const _errs68 = errors;
if(errors === _errs68){
if(Array.isArray(data27)){
var valid15 = true;
const len2 = data27.length;
for(let i2=0; i2<len2; i2++){
let data28 = data27[i2];
const _errs70 = errors;
const _errs71 = errors;
if(errors === _errs71){
if(data28 && typeof data28 == "object" && !Array.isArray(data28)){
let missing10;
if((((((data28.name === undefined) && (missing10 = "name")) || ((data28.usage === undefined) && (missing10 = "usage"))) || ((data28.description === undefined) && (missing10 = "description"))) || ((data28.scope === undefined) && (missing10 = "scope"))) || ((data28.available === undefined) && (missing10 = "available"))){
const err46 = {instancePath:instancePath+"/commands/" + i2,schemaPath:"#/$defs/CommandSpec/required",keyword:"required",params:{missingProperty: missing10},message:"must have required property '"+missing10+"'"};
if(vErrors === null){
vErrors = [err46];
}
else {
vErrors.push(err46);
}
errors++;
}
else {
if(data28.available !== undefined){
const _errs73 = errors;
if(typeof data28.available !== "boolean"){
const err47 = {instancePath:instancePath+"/commands/" + i2+"/available",schemaPath:"#/$defs/CommandSpec/properties/available/type",keyword:"type",params:{type: "boolean"},message:"must be boolean"};
if(vErrors === null){
vErrors = [err47];
}
else {
vErrors.push(err47);
}
errors++;
}
var valid17 = _errs73 === errors;
}
else {
var valid17 = true;
}
if(valid17){
if(data28.capability !== undefined){
let data30 = data28.capability;
const _errs75 = errors;
if((typeof data30 !== "string") && (data30 !== null)){
const err48 = {instancePath:instancePath+"/commands/" + i2+"/capability",schemaPath:"#/$defs/CommandSpec/properties/capability/type",keyword:"type",params:{type: schema83.properties.capability.type},message:"must be string,null"};
if(vErrors === null){
vErrors = [err48];
}
else {
vErrors.push(err48);
}
errors++;
}
var valid17 = _errs75 === errors;
}
else {
var valid17 = true;
}
if(valid17){
if(data28.description !== undefined){
const _errs77 = errors;
if(typeof data28.description !== "string"){
const err49 = {instancePath:instancePath+"/commands/" + i2+"/description",schemaPath:"#/$defs/CommandSpec/properties/description/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err49];
}
else {
vErrors.push(err49);
}
errors++;
}
var valid17 = _errs77 === errors;
}
else {
var valid17 = true;
}
if(valid17){
if(data28.name !== undefined){
const _errs79 = errors;
if(typeof data28.name !== "string"){
const err50 = {instancePath:instancePath+"/commands/" + i2+"/name",schemaPath:"#/$defs/CommandSpec/properties/name/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err50];
}
else {
vErrors.push(err50);
}
errors++;
}
var valid17 = _errs79 === errors;
}
else {
var valid17 = true;
}
if(valid17){
if(data28.scope !== undefined){
const _errs81 = errors;
if(typeof data28.scope !== "string"){
const err51 = {instancePath:instancePath+"/commands/" + i2+"/scope",schemaPath:"#/$defs/CommandSpec/properties/scope/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err51];
}
else {
vErrors.push(err51);
}
errors++;
}
var valid17 = _errs81 === errors;
}
else {
var valid17 = true;
}
if(valid17){
if(data28.usage !== undefined){
const _errs83 = errors;
if(typeof data28.usage !== "string"){
const err52 = {instancePath:instancePath+"/commands/" + i2+"/usage",schemaPath:"#/$defs/CommandSpec/properties/usage/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err52];
}
else {
vErrors.push(err52);
}
errors++;
}
var valid17 = _errs83 === errors;
}
else {
var valid17 = true;
}
}
}
}
}
}
}
}
else {
const err53 = {instancePath:instancePath+"/commands/" + i2,schemaPath:"#/$defs/CommandSpec/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err53];
}
else {
vErrors.push(err53);
}
errors++;
}
}
var valid15 = _errs70 === errors;
if(!valid15){
break;
}
}
}
else {
const err54 = {instancePath:instancePath+"/commands",schemaPath:"#/oneOf/7/properties/commands/type",keyword:"type",params:{type: "array"},message:"must be array"};
if(vErrors === null){
vErrors = [err54];
}
else {
vErrors.push(err54);
}
errors++;
}
}
var valid14 = _errs68 === errors;
}
else {
var valid14 = true;
}
if(valid14){
if(data.kind !== undefined){
let data35 = data.kind;
const _errs85 = errors;
if(typeof data35 !== "string"){
const err55 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/7/properties/kind/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err55];
}
else {
vErrors.push(err55);
}
errors++;
}
if("catalogue" !== data35){
const err56 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/7/properties/kind/const",keyword:"const",params:{allowedValue: "catalogue"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err56];
}
else {
vErrors.push(err56);
}
errors++;
}
var valid14 = _errs85 === errors;
}
else {
var valid14 = true;
}
}
}
}
else {
const err57 = {instancePath,schemaPath:"#/oneOf/7/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err57];
}
else {
vErrors.push(err57);
}
errors++;
}
}
var _valid0 = _errs66 === errors;
if(_valid0 && valid0){
valid0 = false;
passing0 = [passing0, 7];
}
else {
if(_valid0){
valid0 = true;
passing0 = 7;
if(props1 !== true){
props1 = props1 || {};
props1.commands = true;
props1.kind = true;
}
}
const _errs87 = errors;
if(errors === _errs87){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing11;
if((((data.kind === undefined) && (missing11 = "kind")) || ((data.conversations === undefined) && (missing11 = "conversations"))) || ((data.revision === undefined) && (missing11 = "revision"))){
const err58 = {instancePath,schemaPath:"#/oneOf/8/required",keyword:"required",params:{missingProperty: missing11},message:"must have required property '"+missing11+"'"};
if(vErrors === null){
vErrors = [err58];
}
else {
vErrors.push(err58);
}
errors++;
}
else {
if(data.conversations !== undefined){
let data36 = data.conversations;
const _errs89 = errors;
if(errors === _errs89){
if(Array.isArray(data36)){
var valid19 = true;
const len3 = data36.length;
for(let i3=0; i3<len3; i3++){
const _errs91 = errors;
if(!(validate77(data36[i3], {instancePath:instancePath+"/conversations/" + i3,parentData:data36,parentDataProperty:i3,rootData,dynamicAnchors}))){
vErrors = vErrors === null ? validate77.errors : vErrors.concat(validate77.errors);
errors = vErrors.length;
}
var valid19 = _errs91 === errors;
if(!valid19){
break;
}
}
}
else {
const err59 = {instancePath:instancePath+"/conversations",schemaPath:"#/oneOf/8/properties/conversations/type",keyword:"type",params:{type: "array"},message:"must be array"};
if(vErrors === null){
vErrors = [err59];
}
else {
vErrors.push(err59);
}
errors++;
}
}
var valid18 = _errs89 === errors;
}
else {
var valid18 = true;
}
if(valid18){
if(data.kind !== undefined){
let data38 = data.kind;
const _errs92 = errors;
if(typeof data38 !== "string"){
const err60 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/8/properties/kind/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err60];
}
else {
vErrors.push(err60);
}
errors++;
}
if("projection" !== data38){
const err61 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/8/properties/kind/const",keyword:"const",params:{allowedValue: "projection"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err61];
}
else {
vErrors.push(err61);
}
errors++;
}
var valid18 = _errs92 === errors;
}
else {
var valid18 = true;
}
if(valid18){
if(data.revision !== undefined){
const _errs94 = errors;
if(typeof data.revision !== "string"){
const err62 = {instancePath:instancePath+"/revision",schemaPath:"#/oneOf/8/properties/revision/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err62];
}
else {
vErrors.push(err62);
}
errors++;
}
var valid18 = _errs94 === errors;
}
else {
var valid18 = true;
}
}
}
}
}
else {
const err63 = {instancePath,schemaPath:"#/oneOf/8/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err63];
}
else {
vErrors.push(err63);
}
errors++;
}
}
var _valid0 = _errs87 === errors;
if(_valid0 && valid0){
valid0 = false;
passing0 = [passing0, 8];
}
else {
if(_valid0){
valid0 = true;
passing0 = 8;
if(props1 !== true){
props1 = props1 || {};
props1.conversations = true;
props1.kind = true;
props1.revision = true;
}
}
const _errs96 = errors;
if(errors === _errs96){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing12;
if(((data.kind === undefined) && (missing12 = "kind")) || ((data.output === undefined) && (missing12 = "output"))){
const err64 = {instancePath,schemaPath:"#/oneOf/9/required",keyword:"required",params:{missingProperty: missing12},message:"must have required property '"+missing12+"'"};
if(vErrors === null){
vErrors = [err64];
}
else {
vErrors.push(err64);
}
errors++;
}
else {
if(data.conversation !== undefined){
let data40 = data.conversation;
const _errs98 = errors;
if((typeof data40 !== "string") && (data40 !== null)){
const err65 = {instancePath:instancePath+"/conversation",schemaPath:"#/oneOf/9/properties/conversation/type",keyword:"type",params:{type: schema75.oneOf[9].properties.conversation.type},message:"must be string,null"};
if(vErrors === null){
vErrors = [err65];
}
else {
vErrors.push(err65);
}
errors++;
}
var valid20 = _errs98 === errors;
}
else {
var valid20 = true;
}
if(valid20){
if(data.kind !== undefined){
let data41 = data.kind;
const _errs100 = errors;
if(typeof data41 !== "string"){
const err66 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/9/properties/kind/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err66];
}
else {
vErrors.push(err66);
}
errors++;
}
if("output" !== data41){
const err67 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/9/properties/kind/const",keyword:"const",params:{allowedValue: "output"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err67];
}
else {
vErrors.push(err67);
}
errors++;
}
var valid20 = _errs100 === errors;
}
else {
var valid20 = true;
}
if(valid20){
if(data.output !== undefined){
const _errs102 = errors;
if(!(validate80(data.output, {instancePath:instancePath+"/output",parentData:data,parentDataProperty:"output",rootData,dynamicAnchors}))){
vErrors = vErrors === null ? validate80.errors : vErrors.concat(validate80.errors);
errors = vErrors.length;
}
var valid20 = _errs102 === errors;
}
else {
var valid20 = true;
}
}
}
}
}
else {
const err68 = {instancePath,schemaPath:"#/oneOf/9/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err68];
}
else {
vErrors.push(err68);
}
errors++;
}
}
var _valid0 = _errs96 === errors;
if(_valid0 && valid0){
valid0 = false;
passing0 = [passing0, 9];
}
else {
if(_valid0){
valid0 = true;
passing0 = 9;
if(props1 !== true){
props1 = props1 || {};
props1.conversation = true;
props1.kind = true;
props1.output = true;
}
}
const _errs103 = errors;
if(errors === _errs103){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing13;
if((data.kind === undefined) && (missing13 = "kind")){
const err69 = {instancePath,schemaPath:"#/oneOf/10/required",keyword:"required",params:{missingProperty: missing13},message:"must have required property '"+missing13+"'"};
if(vErrors === null){
vErrors = [err69];
}
else {
vErrors.push(err69);
}
errors++;
}
else {
if(data.conversation !== undefined){
let data43 = data.conversation;
const _errs105 = errors;
if((typeof data43 !== "string") && (data43 !== null)){
const err70 = {instancePath:instancePath+"/conversation",schemaPath:"#/oneOf/10/properties/conversation/type",keyword:"type",params:{type: schema75.oneOf[10].properties.conversation.type},message:"must be string,null"};
if(vErrors === null){
vErrors = [err70];
}
else {
vErrors.push(err70);
}
errors++;
}
var valid21 = _errs105 === errors;
}
else {
var valid21 = true;
}
if(valid21){
if(data.kind !== undefined){
let data44 = data.kind;
const _errs107 = errors;
if(typeof data44 !== "string"){
const err71 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/10/properties/kind/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err71];
}
else {
vErrors.push(err71);
}
errors++;
}
if("applied" !== data44){
const err72 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/10/properties/kind/const",keyword:"const",params:{allowedValue: "applied"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err72];
}
else {
vErrors.push(err72);
}
errors++;
}
var valid21 = _errs107 === errors;
}
else {
var valid21 = true;
}
if(valid21){
if(data.notice !== undefined){
let data45 = data.notice;
const _errs109 = errors;
if((typeof data45 !== "string") && (data45 !== null)){
const err73 = {instancePath:instancePath+"/notice",schemaPath:"#/oneOf/10/properties/notice/type",keyword:"type",params:{type: schema75.oneOf[10].properties.notice.type},message:"must be string,null"};
if(vErrors === null){
vErrors = [err73];
}
else {
vErrors.push(err73);
}
errors++;
}
var valid21 = _errs109 === errors;
}
else {
var valid21 = true;
}
}
}
}
}
else {
const err74 = {instancePath,schemaPath:"#/oneOf/10/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err74];
}
else {
vErrors.push(err74);
}
errors++;
}
}
var _valid0 = _errs103 === errors;
if(_valid0 && valid0){
valid0 = false;
passing0 = [passing0, 10];
}
else {
if(_valid0){
valid0 = true;
passing0 = 10;
if(props1 !== true){
props1 = props1 || {};
props1.conversation = true;
props1.kind = true;
props1.notice = true;
}
}
const _errs111 = errors;
if(errors === _errs111){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing14;
if(((data.kind === undefined) && (missing14 = "kind")) || ((data.revision === undefined) && (missing14 = "revision"))){
const err75 = {instancePath,schemaPath:"#/oneOf/11/required",keyword:"required",params:{missingProperty: missing14},message:"must have required property '"+missing14+"'"};
if(vErrors === null){
vErrors = [err75];
}
else {
vErrors.push(err75);
}
errors++;
}
else {
if(data.kind !== undefined){
let data46 = data.kind;
const _errs113 = errors;
if(typeof data46 !== "string"){
const err76 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/11/properties/kind/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err76];
}
else {
vErrors.push(err76);
}
errors++;
}
if("changed" !== data46){
const err77 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/11/properties/kind/const",keyword:"const",params:{allowedValue: "changed"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err77];
}
else {
vErrors.push(err77);
}
errors++;
}
var valid22 = _errs113 === errors;
}
else {
var valid22 = true;
}
if(valid22){
if(data.revision !== undefined){
const _errs115 = errors;
if(typeof data.revision !== "string"){
const err78 = {instancePath:instancePath+"/revision",schemaPath:"#/oneOf/11/properties/revision/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err78];
}
else {
vErrors.push(err78);
}
errors++;
}
var valid22 = _errs115 === errors;
}
else {
var valid22 = true;
}
}
}
}
else {
const err79 = {instancePath,schemaPath:"#/oneOf/11/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err79];
}
else {
vErrors.push(err79);
}
errors++;
}
}
var _valid0 = _errs111 === errors;
if(_valid0 && valid0){
valid0 = false;
passing0 = [passing0, 11];
}
else {
if(_valid0){
valid0 = true;
passing0 = 11;
if(props1 !== true){
props1 = props1 || {};
props1.kind = true;
props1.revision = true;
}
}
const _errs117 = errors;
if(errors === _errs117){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing15;
if((((data.kind === undefined) && (missing15 = "kind")) || ((data.code === undefined) && (missing15 = "code"))) || ((data.message === undefined) && (missing15 = "message"))){
const err80 = {instancePath,schemaPath:"#/oneOf/12/required",keyword:"required",params:{missingProperty: missing15},message:"must have required property '"+missing15+"'"};
if(vErrors === null){
vErrors = [err80];
}
else {
vErrors.push(err80);
}
errors++;
}
else {
if(data.code !== undefined){
const _errs119 = errors;
if(typeof data.code !== "string"){
const err81 = {instancePath:instancePath+"/code",schemaPath:"#/oneOf/12/properties/code/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err81];
}
else {
vErrors.push(err81);
}
errors++;
}
var valid23 = _errs119 === errors;
}
else {
var valid23 = true;
}
if(valid23){
if(data.kind !== undefined){
let data49 = data.kind;
const _errs121 = errors;
if(typeof data49 !== "string"){
const err82 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/12/properties/kind/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err82];
}
else {
vErrors.push(err82);
}
errors++;
}
if("error" !== data49){
const err83 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/12/properties/kind/const",keyword:"const",params:{allowedValue: "error"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err83];
}
else {
vErrors.push(err83);
}
errors++;
}
var valid23 = _errs121 === errors;
}
else {
var valid23 = true;
}
if(valid23){
if(data.message !== undefined){
const _errs123 = errors;
if(typeof data.message !== "string"){
const err84 = {instancePath:instancePath+"/message",schemaPath:"#/oneOf/12/properties/message/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err84];
}
else {
vErrors.push(err84);
}
errors++;
}
var valid23 = _errs123 === errors;
}
else {
var valid23 = true;
}
}
}
}
}
else {
const err85 = {instancePath,schemaPath:"#/oneOf/12/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err85];
}
else {
vErrors.push(err85);
}
errors++;
}
}
var _valid0 = _errs117 === errors;
if(_valid0 && valid0){
valid0 = false;
passing0 = [passing0, 12];
}
else {
if(_valid0){
valid0 = true;
passing0 = 12;
if(props1 !== true){
props1 = props1 || {};
props1.code = true;
props1.kind = true;
props1.message = true;
}
}
}
}
}
}
}
}
}
}
}
}
}
}
if(!valid0){
const err86 = {instancePath,schemaPath:"#/oneOf",keyword:"oneOf",params:{passingSchemas: passing0},message:"must match exactly one schema in oneOf"};
if(vErrors === null){
vErrors = [err86];
}
else {
vErrors.push(err86);
}
errors++;
validate70.errors = vErrors;
return false;
}
else {
errors = _errs0;
if(vErrors !== null){
if(_errs0){
vErrors.length = _errs0;
}
else {
vErrors = null;
}
}
}
validate70.errors = vErrors;
evaluated0.props = props1;
return errors === 0;
}
validate70.evaluated = {"dynamicProps":true,"dynamicItems":false};


function validate62(data, {instancePath="", parentData, parentDataProperty, rootData=data, dynamicAnchors={}}={}){
let vErrors = null;
let errors = 0;
const evaluated0 = validate62.evaluated;
if(evaluated0.dynamicProps){
evaluated0.props = undefined;
}
if(evaluated0.dynamicItems){
evaluated0.items = undefined;
}
const _errs0 = errors;
let valid0 = false;
let passing0 = null;
const _errs1 = errors;
if(errors === _errs1){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing0;
if(((data.kind === undefined) && (missing0 = "kind")) || ((data.networks === undefined) && (missing0 = "networks"))){
const err0 = {instancePath,schemaPath:"#/oneOf/0/required",keyword:"required",params:{missingProperty: missing0},message:"must have required property '"+missing0+"'"};
if(vErrors === null){
vErrors = [err0];
}
else {
vErrors.push(err0);
}
errors++;
}
else {
if(data.kind !== undefined){
let data0 = data.kind;
const _errs3 = errors;
if(typeof data0 !== "string"){
const err1 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/0/properties/kind/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err1];
}
else {
vErrors.push(err1);
}
errors++;
}
if("list" !== data0){
const err2 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/0/properties/kind/const",keyword:"const",params:{allowedValue: "list"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err2];
}
else {
vErrors.push(err2);
}
errors++;
}
var valid1 = _errs3 === errors;
}
else {
var valid1 = true;
}
if(valid1){
if(data.networks !== undefined){
let data1 = data.networks;
const _errs5 = errors;
if(errors === _errs5){
if(Array.isArray(data1)){
var valid2 = true;
const len0 = data1.length;
for(let i0=0; i0<len0; i0++){
const _errs7 = errors;
if(!(validate63(data1[i0], {instancePath:instancePath+"/networks/" + i0,parentData:data1,parentDataProperty:i0,rootData,dynamicAnchors}))){
vErrors = vErrors === null ? validate63.errors : vErrors.concat(validate63.errors);
errors = vErrors.length;
}
var valid2 = _errs7 === errors;
if(!valid2){
break;
}
}
}
else {
const err3 = {instancePath:instancePath+"/networks",schemaPath:"#/oneOf/0/properties/networks/type",keyword:"type",params:{type: "array"},message:"must be array"};
if(vErrors === null){
vErrors = [err3];
}
else {
vErrors.push(err3);
}
errors++;
}
}
var valid1 = _errs5 === errors;
}
else {
var valid1 = true;
}
}
}
}
else {
const err4 = {instancePath,schemaPath:"#/oneOf/0/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err4];
}
else {
vErrors.push(err4);
}
errors++;
}
}
var _valid0 = _errs1 === errors;
if(_valid0){
valid0 = true;
passing0 = 0;
var props0 = {};
props0.kind = true;
props0.networks = true;
}
const _errs8 = errors;
if(errors === _errs8){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing1;
if(((data.kind === undefined) && (missing1 = "kind")) || ((data.preview === undefined) && (missing1 = "preview"))){
const err5 = {instancePath,schemaPath:"#/oneOf/1/required",keyword:"required",params:{missingProperty: missing1},message:"must have required property '"+missing1+"'"};
if(vErrors === null){
vErrors = [err5];
}
else {
vErrors.push(err5);
}
errors++;
}
else {
if(data.kind !== undefined){
let data3 = data.kind;
const _errs10 = errors;
if(typeof data3 !== "string"){
const err6 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/1/properties/kind/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err6];
}
else {
vErrors.push(err6);
}
errors++;
}
if("preview" !== data3){
const err7 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/1/properties/kind/const",keyword:"const",params:{allowedValue: "preview"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err7];
}
else {
vErrors.push(err7);
}
errors++;
}
var valid3 = _errs10 === errors;
}
else {
var valid3 = true;
}
if(valid3){
if(data.preview !== undefined){
const _errs12 = errors;
if(!(validate67(data.preview, {instancePath:instancePath+"/preview",parentData:data,parentDataProperty:"preview",rootData,dynamicAnchors}))){
vErrors = vErrors === null ? validate67.errors : vErrors.concat(validate67.errors);
errors = vErrors.length;
}
var valid3 = _errs12 === errors;
}
else {
var valid3 = true;
}
}
}
}
else {
const err8 = {instancePath,schemaPath:"#/oneOf/1/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err8];
}
else {
vErrors.push(err8);
}
errors++;
}
}
var _valid0 = _errs8 === errors;
if(_valid0 && valid0){
valid0 = false;
passing0 = [passing0, 1];
}
else {
if(_valid0){
valid0 = true;
passing0 = 1;
if(props0 !== true){
props0 = props0 || {};
props0.kind = true;
props0.preview = true;
}
}
const _errs13 = errors;
if(errors === _errs13){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing2;
if((((data.kind === undefined) && (missing2 = "kind")) || ((data.network === undefined) && (missing2 = "network"))) || ((data.response === undefined) && (missing2 = "response"))){
const err9 = {instancePath,schemaPath:"#/oneOf/2/required",keyword:"required",params:{missingProperty: missing2},message:"must have required property '"+missing2+"'"};
if(vErrors === null){
vErrors = [err9];
}
else {
vErrors.push(err9);
}
errors++;
}
else {
if(data.kind !== undefined){
let data5 = data.kind;
const _errs15 = errors;
if(typeof data5 !== "string"){
const err10 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/2/properties/kind/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err10];
}
else {
vErrors.push(err10);
}
errors++;
}
if("result" !== data5){
const err11 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/2/properties/kind/const",keyword:"const",params:{allowedValue: "result"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err11];
}
else {
vErrors.push(err11);
}
errors++;
}
var valid4 = _errs15 === errors;
}
else {
var valid4 = true;
}
if(valid4){
if(data.network !== undefined){
const _errs17 = errors;
if(typeof data.network !== "string"){
const err12 = {instancePath:instancePath+"/network",schemaPath:"#/oneOf/2/properties/network/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err12];
}
else {
vErrors.push(err12);
}
errors++;
}
var valid4 = _errs17 === errors;
}
else {
var valid4 = true;
}
if(valid4){
if(data.response !== undefined){
const _errs19 = errors;
if(!(validate70(data.response, {instancePath:instancePath+"/response",parentData:data,parentDataProperty:"response",rootData,dynamicAnchors}))){
vErrors = vErrors === null ? validate70.errors : vErrors.concat(validate70.errors);
errors = vErrors.length;
}
var valid4 = _errs19 === errors;
}
else {
var valid4 = true;
}
}
}
}
}
else {
const err13 = {instancePath,schemaPath:"#/oneOf/2/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err13];
}
else {
vErrors.push(err13);
}
errors++;
}
}
var _valid0 = _errs13 === errors;
if(_valid0 && valid0){
valid0 = false;
passing0 = [passing0, 2];
}
else {
if(_valid0){
valid0 = true;
passing0 = 2;
if(props0 !== true){
props0 = props0 || {};
props0.kind = true;
props0.network = true;
props0.response = true;
}
}
}
}
if(!valid0){
const err14 = {instancePath,schemaPath:"#/oneOf",keyword:"oneOf",params:{passingSchemas: passing0},message:"must match exactly one schema in oneOf"};
if(vErrors === null){
vErrors = [err14];
}
else {
vErrors.push(err14);
}
errors++;
validate62.errors = vErrors;
return false;
}
else {
errors = _errs0;
if(vErrors !== null){
if(_errs0){
vErrors.length = _errs0;
}
else {
vErrors = null;
}
}
}
validate62.errors = vErrors;
evaluated0.props = props0;
return errors === 0;
}
validate62.evaluated = {"dynamicProps":true,"dynamicItems":false};

export const networks_error = validate93;
const schema100 = {"$schema":"https://json-schema.org/draft/2020-12/schema","additionalProperties":false,"properties":{"code":{"type":"string"},"message":{"type":"string"}},"required":["code","message"],"title":"ChatError","type":"object"};

function validate93(data, {instancePath="", parentData, parentDataProperty, rootData=data, dynamicAnchors={}}={}){
let vErrors = null;
let errors = 0;
const evaluated0 = validate93.evaluated;
if(evaluated0.dynamicProps){
evaluated0.props = undefined;
}
if(evaluated0.dynamicItems){
evaluated0.items = undefined;
}
if(errors === 0){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing0;
if(((data.code === undefined) && (missing0 = "code")) || ((data.message === undefined) && (missing0 = "message"))){
validate93.errors = [{instancePath,schemaPath:"#/required",keyword:"required",params:{missingProperty: missing0},message:"must have required property '"+missing0+"'"}];
return false;
}
else {
const _errs1 = errors;
for(const key0 in data){
if(!((key0 === "code") || (key0 === "message"))){
validate93.errors = [{instancePath,schemaPath:"#/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key0},message:"must NOT have additional properties"}];
return false;
break;
}
}
if(_errs1 === errors){
if(data.code !== undefined){
const _errs2 = errors;
if(typeof data.code !== "string"){
validate93.errors = [{instancePath:instancePath+"/code",schemaPath:"#/properties/code/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs2 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.message !== undefined){
const _errs4 = errors;
if(typeof data.message !== "string"){
validate93.errors = [{instancePath:instancePath+"/message",schemaPath:"#/properties/message/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs4 === errors;
}
else {
var valid0 = true;
}
}
}
}
}
else {
validate93.errors = [{instancePath,schemaPath:"#/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
validate93.errors = vErrors;
return errors === 0;
}
validate93.evaluated = {"props":true,"dynamicProps":false,"dynamicItems":false};

export const files_args = validate94;
const schema101 = {"$defs":{"FileRequest":{"oneOf":[{"additionalProperties":false,"properties":{"action":{"const":"list","type":"string"},"conversation":{"type":["string","null"]}},"required":["action"],"type":"object"},{"additionalProperties":false,"properties":{"action":{"const":"prepare","type":"string"},"conversation":{"type":"string"},"id":{"type":"string"},"name":{"type":"string"},"size_bytes":{"type":"string"}},"required":["action","id","conversation","name","size_bytes"],"type":"object"},{"additionalProperties":false,"properties":{"action":{"const":"commit","type":"string"},"id":{"type":"string"}},"required":["action","id"],"type":"object"},{"additionalProperties":false,"properties":{"action":{"const":"accept","type":"string"},"id":{"type":"string"}},"required":["action","id"],"type":"object"},{"additionalProperties":false,"properties":{"action":{"const":"pause","type":"string"},"id":{"type":"string"}},"required":["action","id"],"type":"object"},{"additionalProperties":false,"properties":{"action":{"const":"resume","type":"string"},"id":{"type":"string"}},"required":["action","id"],"type":"object"},{"additionalProperties":false,"properties":{"action":{"const":"cancel","type":"string"},"id":{"type":"string"}},"required":["action","id"],"type":"object"},{"additionalProperties":false,"properties":{"action":{"const":"configure","type":"string"},"quota_bytes":{"type":"string"},"retention_days":{"format":"uint16","maximum":65535,"minimum":0,"type":"integer"}},"required":["action","quota_bytes","retention_days"],"type":"object"}]}},"$schema":"https://json-schema.org/draft/2020-12/schema","additionalProperties":false,"properties":{"request":{"$ref":"#/$defs/FileRequest"}},"required":["request"],"title":"ChatFilesArgs","type":"object"};
const schema102 = {"oneOf":[{"additionalProperties":false,"properties":{"action":{"const":"list","type":"string"},"conversation":{"type":["string","null"]}},"required":["action"],"type":"object"},{"additionalProperties":false,"properties":{"action":{"const":"prepare","type":"string"},"conversation":{"type":"string"},"id":{"type":"string"},"name":{"type":"string"},"size_bytes":{"type":"string"}},"required":["action","id","conversation","name","size_bytes"],"type":"object"},{"additionalProperties":false,"properties":{"action":{"const":"commit","type":"string"},"id":{"type":"string"}},"required":["action","id"],"type":"object"},{"additionalProperties":false,"properties":{"action":{"const":"accept","type":"string"},"id":{"type":"string"}},"required":["action","id"],"type":"object"},{"additionalProperties":false,"properties":{"action":{"const":"pause","type":"string"},"id":{"type":"string"}},"required":["action","id"],"type":"object"},{"additionalProperties":false,"properties":{"action":{"const":"resume","type":"string"},"id":{"type":"string"}},"required":["action","id"],"type":"object"},{"additionalProperties":false,"properties":{"action":{"const":"cancel","type":"string"},"id":{"type":"string"}},"required":["action","id"],"type":"object"},{"additionalProperties":false,"properties":{"action":{"const":"configure","type":"string"},"quota_bytes":{"type":"string"},"retention_days":{"format":"uint16","maximum":65535,"minimum":0,"type":"integer"}},"required":["action","quota_bytes","retention_days"],"type":"object"}]};

function validate94(data, {instancePath="", parentData, parentDataProperty, rootData=data, dynamicAnchors={}}={}){
let vErrors = null;
let errors = 0;
const evaluated0 = validate94.evaluated;
if(evaluated0.dynamicProps){
evaluated0.props = undefined;
}
if(evaluated0.dynamicItems){
evaluated0.items = undefined;
}
if(errors === 0){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing0;
if((data.request === undefined) && (missing0 = "request")){
validate94.errors = [{instancePath,schemaPath:"#/required",keyword:"required",params:{missingProperty: missing0},message:"must have required property '"+missing0+"'"}];
return false;
}
else {
const _errs1 = errors;
for(const key0 in data){
if(!(key0 === "request")){
validate94.errors = [{instancePath,schemaPath:"#/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key0},message:"must NOT have additional properties"}];
return false;
break;
}
}
if(_errs1 === errors){
if(data.request !== undefined){
let data0 = data.request;
const _errs4 = errors;
let valid2 = false;
let passing0 = null;
const _errs5 = errors;
if(errors === _errs5){
if(data0 && typeof data0 == "object" && !Array.isArray(data0)){
let missing1;
if((data0.action === undefined) && (missing1 = "action")){
const err0 = {instancePath:instancePath+"/request",schemaPath:"#/$defs/FileRequest/oneOf/0/required",keyword:"required",params:{missingProperty: missing1},message:"must have required property '"+missing1+"'"};
if(vErrors === null){
vErrors = [err0];
}
else {
vErrors.push(err0);
}
errors++;
}
else {
const _errs7 = errors;
for(const key1 in data0){
if(!((key1 === "action") || (key1 === "conversation"))){
const err1 = {instancePath:instancePath+"/request",schemaPath:"#/$defs/FileRequest/oneOf/0/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key1},message:"must NOT have additional properties"};
if(vErrors === null){
vErrors = [err1];
}
else {
vErrors.push(err1);
}
errors++;
break;
}
}
if(_errs7 === errors){
if(data0.action !== undefined){
let data1 = data0.action;
const _errs8 = errors;
if(typeof data1 !== "string"){
const err2 = {instancePath:instancePath+"/request/action",schemaPath:"#/$defs/FileRequest/oneOf/0/properties/action/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err2];
}
else {
vErrors.push(err2);
}
errors++;
}
if("list" !== data1){
const err3 = {instancePath:instancePath+"/request/action",schemaPath:"#/$defs/FileRequest/oneOf/0/properties/action/const",keyword:"const",params:{allowedValue: "list"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err3];
}
else {
vErrors.push(err3);
}
errors++;
}
var valid3 = _errs8 === errors;
}
else {
var valid3 = true;
}
if(valid3){
if(data0.conversation !== undefined){
let data2 = data0.conversation;
const _errs10 = errors;
if((typeof data2 !== "string") && (data2 !== null)){
const err4 = {instancePath:instancePath+"/request/conversation",schemaPath:"#/$defs/FileRequest/oneOf/0/properties/conversation/type",keyword:"type",params:{type: schema102.oneOf[0].properties.conversation.type},message:"must be string,null"};
if(vErrors === null){
vErrors = [err4];
}
else {
vErrors.push(err4);
}
errors++;
}
var valid3 = _errs10 === errors;
}
else {
var valid3 = true;
}
}
}
}
}
else {
const err5 = {instancePath:instancePath+"/request",schemaPath:"#/$defs/FileRequest/oneOf/0/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err5];
}
else {
vErrors.push(err5);
}
errors++;
}
}
var _valid0 = _errs5 === errors;
if(_valid0){
valid2 = true;
passing0 = 0;
var props0 = true;
}
const _errs12 = errors;
if(errors === _errs12){
if(data0 && typeof data0 == "object" && !Array.isArray(data0)){
let missing2;
if((((((data0.action === undefined) && (missing2 = "action")) || ((data0.id === undefined) && (missing2 = "id"))) || ((data0.conversation === undefined) && (missing2 = "conversation"))) || ((data0.name === undefined) && (missing2 = "name"))) || ((data0.size_bytes === undefined) && (missing2 = "size_bytes"))){
const err6 = {instancePath:instancePath+"/request",schemaPath:"#/$defs/FileRequest/oneOf/1/required",keyword:"required",params:{missingProperty: missing2},message:"must have required property '"+missing2+"'"};
if(vErrors === null){
vErrors = [err6];
}
else {
vErrors.push(err6);
}
errors++;
}
else {
const _errs14 = errors;
for(const key2 in data0){
if(!(((((key2 === "action") || (key2 === "conversation")) || (key2 === "id")) || (key2 === "name")) || (key2 === "size_bytes"))){
const err7 = {instancePath:instancePath+"/request",schemaPath:"#/$defs/FileRequest/oneOf/1/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key2},message:"must NOT have additional properties"};
if(vErrors === null){
vErrors = [err7];
}
else {
vErrors.push(err7);
}
errors++;
break;
}
}
if(_errs14 === errors){
if(data0.action !== undefined){
let data3 = data0.action;
const _errs15 = errors;
if(typeof data3 !== "string"){
const err8 = {instancePath:instancePath+"/request/action",schemaPath:"#/$defs/FileRequest/oneOf/1/properties/action/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err8];
}
else {
vErrors.push(err8);
}
errors++;
}
if("prepare" !== data3){
const err9 = {instancePath:instancePath+"/request/action",schemaPath:"#/$defs/FileRequest/oneOf/1/properties/action/const",keyword:"const",params:{allowedValue: "prepare"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err9];
}
else {
vErrors.push(err9);
}
errors++;
}
var valid4 = _errs15 === errors;
}
else {
var valid4 = true;
}
if(valid4){
if(data0.conversation !== undefined){
const _errs17 = errors;
if(typeof data0.conversation !== "string"){
const err10 = {instancePath:instancePath+"/request/conversation",schemaPath:"#/$defs/FileRequest/oneOf/1/properties/conversation/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err10];
}
else {
vErrors.push(err10);
}
errors++;
}
var valid4 = _errs17 === errors;
}
else {
var valid4 = true;
}
if(valid4){
if(data0.id !== undefined){
const _errs19 = errors;
if(typeof data0.id !== "string"){
const err11 = {instancePath:instancePath+"/request/id",schemaPath:"#/$defs/FileRequest/oneOf/1/properties/id/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err11];
}
else {
vErrors.push(err11);
}
errors++;
}
var valid4 = _errs19 === errors;
}
else {
var valid4 = true;
}
if(valid4){
if(data0.name !== undefined){
const _errs21 = errors;
if(typeof data0.name !== "string"){
const err12 = {instancePath:instancePath+"/request/name",schemaPath:"#/$defs/FileRequest/oneOf/1/properties/name/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err12];
}
else {
vErrors.push(err12);
}
errors++;
}
var valid4 = _errs21 === errors;
}
else {
var valid4 = true;
}
if(valid4){
if(data0.size_bytes !== undefined){
const _errs23 = errors;
if(typeof data0.size_bytes !== "string"){
const err13 = {instancePath:instancePath+"/request/size_bytes",schemaPath:"#/$defs/FileRequest/oneOf/1/properties/size_bytes/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err13];
}
else {
vErrors.push(err13);
}
errors++;
}
var valid4 = _errs23 === errors;
}
else {
var valid4 = true;
}
}
}
}
}
}
}
}
else {
const err14 = {instancePath:instancePath+"/request",schemaPath:"#/$defs/FileRequest/oneOf/1/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err14];
}
else {
vErrors.push(err14);
}
errors++;
}
}
var _valid0 = _errs12 === errors;
if(_valid0 && valid2){
valid2 = false;
passing0 = [passing0, 1];
}
else {
if(_valid0){
valid2 = true;
passing0 = 1;
if(props0 !== true){
props0 = true;
}
}
const _errs25 = errors;
if(errors === _errs25){
if(data0 && typeof data0 == "object" && !Array.isArray(data0)){
let missing3;
if(((data0.action === undefined) && (missing3 = "action")) || ((data0.id === undefined) && (missing3 = "id"))){
const err15 = {instancePath:instancePath+"/request",schemaPath:"#/$defs/FileRequest/oneOf/2/required",keyword:"required",params:{missingProperty: missing3},message:"must have required property '"+missing3+"'"};
if(vErrors === null){
vErrors = [err15];
}
else {
vErrors.push(err15);
}
errors++;
}
else {
const _errs27 = errors;
for(const key3 in data0){
if(!((key3 === "action") || (key3 === "id"))){
const err16 = {instancePath:instancePath+"/request",schemaPath:"#/$defs/FileRequest/oneOf/2/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key3},message:"must NOT have additional properties"};
if(vErrors === null){
vErrors = [err16];
}
else {
vErrors.push(err16);
}
errors++;
break;
}
}
if(_errs27 === errors){
if(data0.action !== undefined){
let data8 = data0.action;
const _errs28 = errors;
if(typeof data8 !== "string"){
const err17 = {instancePath:instancePath+"/request/action",schemaPath:"#/$defs/FileRequest/oneOf/2/properties/action/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err17];
}
else {
vErrors.push(err17);
}
errors++;
}
if("commit" !== data8){
const err18 = {instancePath:instancePath+"/request/action",schemaPath:"#/$defs/FileRequest/oneOf/2/properties/action/const",keyword:"const",params:{allowedValue: "commit"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err18];
}
else {
vErrors.push(err18);
}
errors++;
}
var valid5 = _errs28 === errors;
}
else {
var valid5 = true;
}
if(valid5){
if(data0.id !== undefined){
const _errs30 = errors;
if(typeof data0.id !== "string"){
const err19 = {instancePath:instancePath+"/request/id",schemaPath:"#/$defs/FileRequest/oneOf/2/properties/id/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err19];
}
else {
vErrors.push(err19);
}
errors++;
}
var valid5 = _errs30 === errors;
}
else {
var valid5 = true;
}
}
}
}
}
else {
const err20 = {instancePath:instancePath+"/request",schemaPath:"#/$defs/FileRequest/oneOf/2/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err20];
}
else {
vErrors.push(err20);
}
errors++;
}
}
var _valid0 = _errs25 === errors;
if(_valid0 && valid2){
valid2 = false;
passing0 = [passing0, 2];
}
else {
if(_valid0){
valid2 = true;
passing0 = 2;
if(props0 !== true){
props0 = true;
}
}
const _errs32 = errors;
if(errors === _errs32){
if(data0 && typeof data0 == "object" && !Array.isArray(data0)){
let missing4;
if(((data0.action === undefined) && (missing4 = "action")) || ((data0.id === undefined) && (missing4 = "id"))){
const err21 = {instancePath:instancePath+"/request",schemaPath:"#/$defs/FileRequest/oneOf/3/required",keyword:"required",params:{missingProperty: missing4},message:"must have required property '"+missing4+"'"};
if(vErrors === null){
vErrors = [err21];
}
else {
vErrors.push(err21);
}
errors++;
}
else {
const _errs34 = errors;
for(const key4 in data0){
if(!((key4 === "action") || (key4 === "id"))){
const err22 = {instancePath:instancePath+"/request",schemaPath:"#/$defs/FileRequest/oneOf/3/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key4},message:"must NOT have additional properties"};
if(vErrors === null){
vErrors = [err22];
}
else {
vErrors.push(err22);
}
errors++;
break;
}
}
if(_errs34 === errors){
if(data0.action !== undefined){
let data10 = data0.action;
const _errs35 = errors;
if(typeof data10 !== "string"){
const err23 = {instancePath:instancePath+"/request/action",schemaPath:"#/$defs/FileRequest/oneOf/3/properties/action/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err23];
}
else {
vErrors.push(err23);
}
errors++;
}
if("accept" !== data10){
const err24 = {instancePath:instancePath+"/request/action",schemaPath:"#/$defs/FileRequest/oneOf/3/properties/action/const",keyword:"const",params:{allowedValue: "accept"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err24];
}
else {
vErrors.push(err24);
}
errors++;
}
var valid6 = _errs35 === errors;
}
else {
var valid6 = true;
}
if(valid6){
if(data0.id !== undefined){
const _errs37 = errors;
if(typeof data0.id !== "string"){
const err25 = {instancePath:instancePath+"/request/id",schemaPath:"#/$defs/FileRequest/oneOf/3/properties/id/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err25];
}
else {
vErrors.push(err25);
}
errors++;
}
var valid6 = _errs37 === errors;
}
else {
var valid6 = true;
}
}
}
}
}
else {
const err26 = {instancePath:instancePath+"/request",schemaPath:"#/$defs/FileRequest/oneOf/3/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err26];
}
else {
vErrors.push(err26);
}
errors++;
}
}
var _valid0 = _errs32 === errors;
if(_valid0 && valid2){
valid2 = false;
passing0 = [passing0, 3];
}
else {
if(_valid0){
valid2 = true;
passing0 = 3;
if(props0 !== true){
props0 = true;
}
}
const _errs39 = errors;
if(errors === _errs39){
if(data0 && typeof data0 == "object" && !Array.isArray(data0)){
let missing5;
if(((data0.action === undefined) && (missing5 = "action")) || ((data0.id === undefined) && (missing5 = "id"))){
const err27 = {instancePath:instancePath+"/request",schemaPath:"#/$defs/FileRequest/oneOf/4/required",keyword:"required",params:{missingProperty: missing5},message:"must have required property '"+missing5+"'"};
if(vErrors === null){
vErrors = [err27];
}
else {
vErrors.push(err27);
}
errors++;
}
else {
const _errs41 = errors;
for(const key5 in data0){
if(!((key5 === "action") || (key5 === "id"))){
const err28 = {instancePath:instancePath+"/request",schemaPath:"#/$defs/FileRequest/oneOf/4/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key5},message:"must NOT have additional properties"};
if(vErrors === null){
vErrors = [err28];
}
else {
vErrors.push(err28);
}
errors++;
break;
}
}
if(_errs41 === errors){
if(data0.action !== undefined){
let data12 = data0.action;
const _errs42 = errors;
if(typeof data12 !== "string"){
const err29 = {instancePath:instancePath+"/request/action",schemaPath:"#/$defs/FileRequest/oneOf/4/properties/action/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err29];
}
else {
vErrors.push(err29);
}
errors++;
}
if("pause" !== data12){
const err30 = {instancePath:instancePath+"/request/action",schemaPath:"#/$defs/FileRequest/oneOf/4/properties/action/const",keyword:"const",params:{allowedValue: "pause"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err30];
}
else {
vErrors.push(err30);
}
errors++;
}
var valid7 = _errs42 === errors;
}
else {
var valid7 = true;
}
if(valid7){
if(data0.id !== undefined){
const _errs44 = errors;
if(typeof data0.id !== "string"){
const err31 = {instancePath:instancePath+"/request/id",schemaPath:"#/$defs/FileRequest/oneOf/4/properties/id/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err31];
}
else {
vErrors.push(err31);
}
errors++;
}
var valid7 = _errs44 === errors;
}
else {
var valid7 = true;
}
}
}
}
}
else {
const err32 = {instancePath:instancePath+"/request",schemaPath:"#/$defs/FileRequest/oneOf/4/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err32];
}
else {
vErrors.push(err32);
}
errors++;
}
}
var _valid0 = _errs39 === errors;
if(_valid0 && valid2){
valid2 = false;
passing0 = [passing0, 4];
}
else {
if(_valid0){
valid2 = true;
passing0 = 4;
if(props0 !== true){
props0 = true;
}
}
const _errs46 = errors;
if(errors === _errs46){
if(data0 && typeof data0 == "object" && !Array.isArray(data0)){
let missing6;
if(((data0.action === undefined) && (missing6 = "action")) || ((data0.id === undefined) && (missing6 = "id"))){
const err33 = {instancePath:instancePath+"/request",schemaPath:"#/$defs/FileRequest/oneOf/5/required",keyword:"required",params:{missingProperty: missing6},message:"must have required property '"+missing6+"'"};
if(vErrors === null){
vErrors = [err33];
}
else {
vErrors.push(err33);
}
errors++;
}
else {
const _errs48 = errors;
for(const key6 in data0){
if(!((key6 === "action") || (key6 === "id"))){
const err34 = {instancePath:instancePath+"/request",schemaPath:"#/$defs/FileRequest/oneOf/5/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key6},message:"must NOT have additional properties"};
if(vErrors === null){
vErrors = [err34];
}
else {
vErrors.push(err34);
}
errors++;
break;
}
}
if(_errs48 === errors){
if(data0.action !== undefined){
let data14 = data0.action;
const _errs49 = errors;
if(typeof data14 !== "string"){
const err35 = {instancePath:instancePath+"/request/action",schemaPath:"#/$defs/FileRequest/oneOf/5/properties/action/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err35];
}
else {
vErrors.push(err35);
}
errors++;
}
if("resume" !== data14){
const err36 = {instancePath:instancePath+"/request/action",schemaPath:"#/$defs/FileRequest/oneOf/5/properties/action/const",keyword:"const",params:{allowedValue: "resume"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err36];
}
else {
vErrors.push(err36);
}
errors++;
}
var valid8 = _errs49 === errors;
}
else {
var valid8 = true;
}
if(valid8){
if(data0.id !== undefined){
const _errs51 = errors;
if(typeof data0.id !== "string"){
const err37 = {instancePath:instancePath+"/request/id",schemaPath:"#/$defs/FileRequest/oneOf/5/properties/id/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err37];
}
else {
vErrors.push(err37);
}
errors++;
}
var valid8 = _errs51 === errors;
}
else {
var valid8 = true;
}
}
}
}
}
else {
const err38 = {instancePath:instancePath+"/request",schemaPath:"#/$defs/FileRequest/oneOf/5/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err38];
}
else {
vErrors.push(err38);
}
errors++;
}
}
var _valid0 = _errs46 === errors;
if(_valid0 && valid2){
valid2 = false;
passing0 = [passing0, 5];
}
else {
if(_valid0){
valid2 = true;
passing0 = 5;
if(props0 !== true){
props0 = true;
}
}
const _errs53 = errors;
if(errors === _errs53){
if(data0 && typeof data0 == "object" && !Array.isArray(data0)){
let missing7;
if(((data0.action === undefined) && (missing7 = "action")) || ((data0.id === undefined) && (missing7 = "id"))){
const err39 = {instancePath:instancePath+"/request",schemaPath:"#/$defs/FileRequest/oneOf/6/required",keyword:"required",params:{missingProperty: missing7},message:"must have required property '"+missing7+"'"};
if(vErrors === null){
vErrors = [err39];
}
else {
vErrors.push(err39);
}
errors++;
}
else {
const _errs55 = errors;
for(const key7 in data0){
if(!((key7 === "action") || (key7 === "id"))){
const err40 = {instancePath:instancePath+"/request",schemaPath:"#/$defs/FileRequest/oneOf/6/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key7},message:"must NOT have additional properties"};
if(vErrors === null){
vErrors = [err40];
}
else {
vErrors.push(err40);
}
errors++;
break;
}
}
if(_errs55 === errors){
if(data0.action !== undefined){
let data16 = data0.action;
const _errs56 = errors;
if(typeof data16 !== "string"){
const err41 = {instancePath:instancePath+"/request/action",schemaPath:"#/$defs/FileRequest/oneOf/6/properties/action/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err41];
}
else {
vErrors.push(err41);
}
errors++;
}
if("cancel" !== data16){
const err42 = {instancePath:instancePath+"/request/action",schemaPath:"#/$defs/FileRequest/oneOf/6/properties/action/const",keyword:"const",params:{allowedValue: "cancel"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err42];
}
else {
vErrors.push(err42);
}
errors++;
}
var valid9 = _errs56 === errors;
}
else {
var valid9 = true;
}
if(valid9){
if(data0.id !== undefined){
const _errs58 = errors;
if(typeof data0.id !== "string"){
const err43 = {instancePath:instancePath+"/request/id",schemaPath:"#/$defs/FileRequest/oneOf/6/properties/id/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err43];
}
else {
vErrors.push(err43);
}
errors++;
}
var valid9 = _errs58 === errors;
}
else {
var valid9 = true;
}
}
}
}
}
else {
const err44 = {instancePath:instancePath+"/request",schemaPath:"#/$defs/FileRequest/oneOf/6/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err44];
}
else {
vErrors.push(err44);
}
errors++;
}
}
var _valid0 = _errs53 === errors;
if(_valid0 && valid2){
valid2 = false;
passing0 = [passing0, 6];
}
else {
if(_valid0){
valid2 = true;
passing0 = 6;
if(props0 !== true){
props0 = true;
}
}
const _errs60 = errors;
if(errors === _errs60){
if(data0 && typeof data0 == "object" && !Array.isArray(data0)){
let missing8;
if((((data0.action === undefined) && (missing8 = "action")) || ((data0.quota_bytes === undefined) && (missing8 = "quota_bytes"))) || ((data0.retention_days === undefined) && (missing8 = "retention_days"))){
const err45 = {instancePath:instancePath+"/request",schemaPath:"#/$defs/FileRequest/oneOf/7/required",keyword:"required",params:{missingProperty: missing8},message:"must have required property '"+missing8+"'"};
if(vErrors === null){
vErrors = [err45];
}
else {
vErrors.push(err45);
}
errors++;
}
else {
const _errs62 = errors;
for(const key8 in data0){
if(!(((key8 === "action") || (key8 === "quota_bytes")) || (key8 === "retention_days"))){
const err46 = {instancePath:instancePath+"/request",schemaPath:"#/$defs/FileRequest/oneOf/7/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key8},message:"must NOT have additional properties"};
if(vErrors === null){
vErrors = [err46];
}
else {
vErrors.push(err46);
}
errors++;
break;
}
}
if(_errs62 === errors){
if(data0.action !== undefined){
let data18 = data0.action;
const _errs63 = errors;
if(typeof data18 !== "string"){
const err47 = {instancePath:instancePath+"/request/action",schemaPath:"#/$defs/FileRequest/oneOf/7/properties/action/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err47];
}
else {
vErrors.push(err47);
}
errors++;
}
if("configure" !== data18){
const err48 = {instancePath:instancePath+"/request/action",schemaPath:"#/$defs/FileRequest/oneOf/7/properties/action/const",keyword:"const",params:{allowedValue: "configure"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err48];
}
else {
vErrors.push(err48);
}
errors++;
}
var valid10 = _errs63 === errors;
}
else {
var valid10 = true;
}
if(valid10){
if(data0.quota_bytes !== undefined){
const _errs65 = errors;
if(typeof data0.quota_bytes !== "string"){
const err49 = {instancePath:instancePath+"/request/quota_bytes",schemaPath:"#/$defs/FileRequest/oneOf/7/properties/quota_bytes/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err49];
}
else {
vErrors.push(err49);
}
errors++;
}
var valid10 = _errs65 === errors;
}
else {
var valid10 = true;
}
if(valid10){
if(data0.retention_days !== undefined){
let data20 = data0.retention_days;
const _errs67 = errors;
if(!(((typeof data20 == "number") && (!(data20 % 1) && !isNaN(data20))) && (isFinite(data20)))){
const err50 = {instancePath:instancePath+"/request/retention_days",schemaPath:"#/$defs/FileRequest/oneOf/7/properties/retention_days/type",keyword:"type",params:{type: "integer"},message:"must be integer"};
if(vErrors === null){
vErrors = [err50];
}
else {
vErrors.push(err50);
}
errors++;
}
if(errors === _errs67){
if((typeof data20 == "number") && (isFinite(data20))){
if(data20 > 65535 || isNaN(data20)){
const err51 = {instancePath:instancePath+"/request/retention_days",schemaPath:"#/$defs/FileRequest/oneOf/7/properties/retention_days/maximum",keyword:"maximum",params:{comparison: "<=", limit: 65535},message:"must be <= 65535"};
if(vErrors === null){
vErrors = [err51];
}
else {
vErrors.push(err51);
}
errors++;
}
else {
if(data20 < 0 || isNaN(data20)){
const err52 = {instancePath:instancePath+"/request/retention_days",schemaPath:"#/$defs/FileRequest/oneOf/7/properties/retention_days/minimum",keyword:"minimum",params:{comparison: ">=", limit: 0},message:"must be >= 0"};
if(vErrors === null){
vErrors = [err52];
}
else {
vErrors.push(err52);
}
errors++;
}
}
}
}
var valid10 = _errs67 === errors;
}
else {
var valid10 = true;
}
}
}
}
}
}
else {
const err53 = {instancePath:instancePath+"/request",schemaPath:"#/$defs/FileRequest/oneOf/7/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err53];
}
else {
vErrors.push(err53);
}
errors++;
}
}
var _valid0 = _errs60 === errors;
if(_valid0 && valid2){
valid2 = false;
passing0 = [passing0, 7];
}
else {
if(_valid0){
valid2 = true;
passing0 = 7;
if(props0 !== true){
props0 = true;
}
}
}
}
}
}
}
}
}
if(!valid2){
const err54 = {instancePath:instancePath+"/request",schemaPath:"#/$defs/FileRequest/oneOf",keyword:"oneOf",params:{passingSchemas: passing0},message:"must match exactly one schema in oneOf"};
if(vErrors === null){
vErrors = [err54];
}
else {
vErrors.push(err54);
}
errors++;
validate94.errors = vErrors;
return false;
}
else {
errors = _errs4;
if(vErrors !== null){
if(_errs4){
vErrors.length = _errs4;
}
else {
vErrors = null;
}
}
}
}
}
}
}
else {
validate94.errors = [{instancePath,schemaPath:"#/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
validate94.errors = vErrors;
return errors === 0;
}
validate94.evaluated = {"props":true,"dynamicProps":false,"dynamicItems":false};

export const files_output = validate95;
const schema103 = {"$defs":{"FileInfo":{"additionalProperties":false,"properties":{"aliases":{"default":null,"items":{"type":"string"},"type":["array","null"]},"completed_by":{"format":"uint16","maximum":65535,"minimum":0,"type":"integer"},"conversation":{"type":"string"},"error":{"type":["string","null"]},"id":{"type":"string"},"name":{"type":"string"},"size_bytes":{"type":"string"},"sources":{"format":"uint16","maximum":65535,"minimum":0,"type":"integer"},"state":{"$ref":"#/$defs/FileState"},"verified_bytes":{"type":"string"},"verified_sources":{"default":0,"description":"Peers contributing verified pieces since this process opened the cache.","format":"uint16","maximum":65535,"minimum":0,"type":"integer"}},"required":["id","conversation","name","size_bytes","verified_bytes","state","sources","completed_by"],"type":"object"},"FileState":{"enum":["offered","importing","downloading","waiting_for_peers","paused","complete","failed","cancelled"],"type":"string"}},"$schema":"https://json-schema.org/draft/2020-12/schema","additionalProperties":false,"properties":{"files":{"items":{"$ref":"#/$defs/FileInfo"},"type":"array"},"quota_bytes":{"type":"string"},"retention_days":{"format":"uint16","maximum":65535,"minimum":0,"type":"integer"},"used_bytes":{"type":"string"}},"required":["files","quota_bytes","used_bytes","retention_days"],"title":"FileSnapshot","type":"object"};
const schema104 = {"additionalProperties":false,"properties":{"aliases":{"default":null,"items":{"type":"string"},"type":["array","null"]},"completed_by":{"format":"uint16","maximum":65535,"minimum":0,"type":"integer"},"conversation":{"type":"string"},"error":{"type":["string","null"]},"id":{"type":"string"},"name":{"type":"string"},"size_bytes":{"type":"string"},"sources":{"format":"uint16","maximum":65535,"minimum":0,"type":"integer"},"state":{"$ref":"#/$defs/FileState"},"verified_bytes":{"type":"string"},"verified_sources":{"default":0,"description":"Peers contributing verified pieces since this process opened the cache.","format":"uint16","maximum":65535,"minimum":0,"type":"integer"}},"required":["id","conversation","name","size_bytes","verified_bytes","state","sources","completed_by"],"type":"object"};
const schema105 = {"enum":["offered","importing","downloading","waiting_for_peers","paused","complete","failed","cancelled"],"type":"string"};

function validate96(data, {instancePath="", parentData, parentDataProperty, rootData=data, dynamicAnchors={}}={}){
let vErrors = null;
let errors = 0;
const evaluated0 = validate96.evaluated;
if(evaluated0.dynamicProps){
evaluated0.props = undefined;
}
if(evaluated0.dynamicItems){
evaluated0.items = undefined;
}
if(errors === 0){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing0;
if(((((((((data.id === undefined) && (missing0 = "id")) || ((data.conversation === undefined) && (missing0 = "conversation"))) || ((data.name === undefined) && (missing0 = "name"))) || ((data.size_bytes === undefined) && (missing0 = "size_bytes"))) || ((data.verified_bytes === undefined) && (missing0 = "verified_bytes"))) || ((data.state === undefined) && (missing0 = "state"))) || ((data.sources === undefined) && (missing0 = "sources"))) || ((data.completed_by === undefined) && (missing0 = "completed_by"))){
validate96.errors = [{instancePath,schemaPath:"#/required",keyword:"required",params:{missingProperty: missing0},message:"must have required property '"+missing0+"'"}];
return false;
}
else {
const _errs1 = errors;
for(const key0 in data){
if(!(func1.call(schema104.properties, key0))){
validate96.errors = [{instancePath,schemaPath:"#/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key0},message:"must NOT have additional properties"}];
return false;
break;
}
}
if(_errs1 === errors){
if(data.aliases !== undefined){
let data0 = data.aliases;
const _errs2 = errors;
if((!(Array.isArray(data0))) && (data0 !== null)){
validate96.errors = [{instancePath:instancePath+"/aliases",schemaPath:"#/properties/aliases/type",keyword:"type",params:{type: schema104.properties.aliases.type},message:"must be array,null"}];
return false;
}
if(errors === _errs2){
if(Array.isArray(data0)){
var valid1 = true;
const len0 = data0.length;
for(let i0=0; i0<len0; i0++){
const _errs4 = errors;
if(typeof data0[i0] !== "string"){
validate96.errors = [{instancePath:instancePath+"/aliases/" + i0,schemaPath:"#/properties/aliases/items/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid1 = _errs4 === errors;
if(!valid1){
break;
}
}
}
}
var valid0 = _errs2 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.completed_by !== undefined){
let data2 = data.completed_by;
const _errs6 = errors;
if(!(((typeof data2 == "number") && (!(data2 % 1) && !isNaN(data2))) && (isFinite(data2)))){
validate96.errors = [{instancePath:instancePath+"/completed_by",schemaPath:"#/properties/completed_by/type",keyword:"type",params:{type: "integer"},message:"must be integer"}];
return false;
}
if(errors === _errs6){
if((typeof data2 == "number") && (isFinite(data2))){
if(data2 > 65535 || isNaN(data2)){
validate96.errors = [{instancePath:instancePath+"/completed_by",schemaPath:"#/properties/completed_by/maximum",keyword:"maximum",params:{comparison: "<=", limit: 65535},message:"must be <= 65535"}];
return false;
}
else {
if(data2 < 0 || isNaN(data2)){
validate96.errors = [{instancePath:instancePath+"/completed_by",schemaPath:"#/properties/completed_by/minimum",keyword:"minimum",params:{comparison: ">=", limit: 0},message:"must be >= 0"}];
return false;
}
}
}
}
var valid0 = _errs6 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.conversation !== undefined){
const _errs8 = errors;
if(typeof data.conversation !== "string"){
validate96.errors = [{instancePath:instancePath+"/conversation",schemaPath:"#/properties/conversation/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs8 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.error !== undefined){
let data4 = data.error;
const _errs10 = errors;
if((typeof data4 !== "string") && (data4 !== null)){
validate96.errors = [{instancePath:instancePath+"/error",schemaPath:"#/properties/error/type",keyword:"type",params:{type: schema104.properties.error.type},message:"must be string,null"}];
return false;
}
var valid0 = _errs10 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.id !== undefined){
const _errs12 = errors;
if(typeof data.id !== "string"){
validate96.errors = [{instancePath:instancePath+"/id",schemaPath:"#/properties/id/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs12 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.name !== undefined){
const _errs14 = errors;
if(typeof data.name !== "string"){
validate96.errors = [{instancePath:instancePath+"/name",schemaPath:"#/properties/name/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs14 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.size_bytes !== undefined){
const _errs16 = errors;
if(typeof data.size_bytes !== "string"){
validate96.errors = [{instancePath:instancePath+"/size_bytes",schemaPath:"#/properties/size_bytes/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs16 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.sources !== undefined){
let data8 = data.sources;
const _errs18 = errors;
if(!(((typeof data8 == "number") && (!(data8 % 1) && !isNaN(data8))) && (isFinite(data8)))){
validate96.errors = [{instancePath:instancePath+"/sources",schemaPath:"#/properties/sources/type",keyword:"type",params:{type: "integer"},message:"must be integer"}];
return false;
}
if(errors === _errs18){
if((typeof data8 == "number") && (isFinite(data8))){
if(data8 > 65535 || isNaN(data8)){
validate96.errors = [{instancePath:instancePath+"/sources",schemaPath:"#/properties/sources/maximum",keyword:"maximum",params:{comparison: "<=", limit: 65535},message:"must be <= 65535"}];
return false;
}
else {
if(data8 < 0 || isNaN(data8)){
validate96.errors = [{instancePath:instancePath+"/sources",schemaPath:"#/properties/sources/minimum",keyword:"minimum",params:{comparison: ">=", limit: 0},message:"must be >= 0"}];
return false;
}
}
}
}
var valid0 = _errs18 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.state !== undefined){
let data9 = data.state;
const _errs20 = errors;
if(typeof data9 !== "string"){
validate96.errors = [{instancePath:instancePath+"/state",schemaPath:"#/$defs/FileState/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
if(!((((((((data9 === "offered") || (data9 === "importing")) || (data9 === "downloading")) || (data9 === "waiting_for_peers")) || (data9 === "paused")) || (data9 === "complete")) || (data9 === "failed")) || (data9 === "cancelled"))){
validate96.errors = [{instancePath:instancePath+"/state",schemaPath:"#/$defs/FileState/enum",keyword:"enum",params:{allowedValues: schema105.enum},message:"must be equal to one of the allowed values"}];
return false;
}
var valid0 = _errs20 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.verified_bytes !== undefined){
const _errs23 = errors;
if(typeof data.verified_bytes !== "string"){
validate96.errors = [{instancePath:instancePath+"/verified_bytes",schemaPath:"#/properties/verified_bytes/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs23 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.verified_sources !== undefined){
let data11 = data.verified_sources;
const _errs25 = errors;
if(!(((typeof data11 == "number") && (!(data11 % 1) && !isNaN(data11))) && (isFinite(data11)))){
validate96.errors = [{instancePath:instancePath+"/verified_sources",schemaPath:"#/properties/verified_sources/type",keyword:"type",params:{type: "integer"},message:"must be integer"}];
return false;
}
if(errors === _errs25){
if((typeof data11 == "number") && (isFinite(data11))){
if(data11 > 65535 || isNaN(data11)){
validate96.errors = [{instancePath:instancePath+"/verified_sources",schemaPath:"#/properties/verified_sources/maximum",keyword:"maximum",params:{comparison: "<=", limit: 65535},message:"must be <= 65535"}];
return false;
}
else {
if(data11 < 0 || isNaN(data11)){
validate96.errors = [{instancePath:instancePath+"/verified_sources",schemaPath:"#/properties/verified_sources/minimum",keyword:"minimum",params:{comparison: ">=", limit: 0},message:"must be >= 0"}];
return false;
}
}
}
}
var valid0 = _errs25 === errors;
}
else {
var valid0 = true;
}
}
}
}
}
}
}
}
}
}
}
}
}
}
else {
validate96.errors = [{instancePath,schemaPath:"#/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
validate96.errors = vErrors;
return errors === 0;
}
validate96.evaluated = {"props":true,"dynamicProps":false,"dynamicItems":false};


function validate95(data, {instancePath="", parentData, parentDataProperty, rootData=data, dynamicAnchors={}}={}){
let vErrors = null;
let errors = 0;
const evaluated0 = validate95.evaluated;
if(evaluated0.dynamicProps){
evaluated0.props = undefined;
}
if(evaluated0.dynamicItems){
evaluated0.items = undefined;
}
if(errors === 0){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing0;
if(((((data.files === undefined) && (missing0 = "files")) || ((data.quota_bytes === undefined) && (missing0 = "quota_bytes"))) || ((data.used_bytes === undefined) && (missing0 = "used_bytes"))) || ((data.retention_days === undefined) && (missing0 = "retention_days"))){
validate95.errors = [{instancePath,schemaPath:"#/required",keyword:"required",params:{missingProperty: missing0},message:"must have required property '"+missing0+"'"}];
return false;
}
else {
const _errs1 = errors;
for(const key0 in data){
if(!((((key0 === "files") || (key0 === "quota_bytes")) || (key0 === "retention_days")) || (key0 === "used_bytes"))){
validate95.errors = [{instancePath,schemaPath:"#/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key0},message:"must NOT have additional properties"}];
return false;
break;
}
}
if(_errs1 === errors){
if(data.files !== undefined){
let data0 = data.files;
const _errs2 = errors;
if(errors === _errs2){
if(Array.isArray(data0)){
var valid1 = true;
const len0 = data0.length;
for(let i0=0; i0<len0; i0++){
const _errs4 = errors;
if(!(validate96(data0[i0], {instancePath:instancePath+"/files/" + i0,parentData:data0,parentDataProperty:i0,rootData,dynamicAnchors}))){
vErrors = vErrors === null ? validate96.errors : vErrors.concat(validate96.errors);
errors = vErrors.length;
}
var valid1 = _errs4 === errors;
if(!valid1){
break;
}
}
}
else {
validate95.errors = [{instancePath:instancePath+"/files",schemaPath:"#/properties/files/type",keyword:"type",params:{type: "array"},message:"must be array"}];
return false;
}
}
var valid0 = _errs2 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.quota_bytes !== undefined){
const _errs5 = errors;
if(typeof data.quota_bytes !== "string"){
validate95.errors = [{instancePath:instancePath+"/quota_bytes",schemaPath:"#/properties/quota_bytes/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs5 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.retention_days !== undefined){
let data3 = data.retention_days;
const _errs7 = errors;
if(!(((typeof data3 == "number") && (!(data3 % 1) && !isNaN(data3))) && (isFinite(data3)))){
validate95.errors = [{instancePath:instancePath+"/retention_days",schemaPath:"#/properties/retention_days/type",keyword:"type",params:{type: "integer"},message:"must be integer"}];
return false;
}
if(errors === _errs7){
if((typeof data3 == "number") && (isFinite(data3))){
if(data3 > 65535 || isNaN(data3)){
validate95.errors = [{instancePath:instancePath+"/retention_days",schemaPath:"#/properties/retention_days/maximum",keyword:"maximum",params:{comparison: "<=", limit: 65535},message:"must be <= 65535"}];
return false;
}
else {
if(data3 < 0 || isNaN(data3)){
validate95.errors = [{instancePath:instancePath+"/retention_days",schemaPath:"#/properties/retention_days/minimum",keyword:"minimum",params:{comparison: ">=", limit: 0},message:"must be >= 0"}];
return false;
}
}
}
}
var valid0 = _errs7 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.used_bytes !== undefined){
const _errs9 = errors;
if(typeof data.used_bytes !== "string"){
validate95.errors = [{instancePath:instancePath+"/used_bytes",schemaPath:"#/properties/used_bytes/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs9 === errors;
}
else {
var valid0 = true;
}
}
}
}
}
}
}
else {
validate95.errors = [{instancePath,schemaPath:"#/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
validate95.errors = vErrors;
return errors === 0;
}
validate95.evaluated = {"props":true,"dynamicProps":false,"dynamicItems":false};

export const files_error = validate98;
const schema106 = {"$schema":"https://json-schema.org/draft/2020-12/schema","additionalProperties":false,"properties":{"code":{"type":"string"},"message":{"type":"string"}},"required":["code","message"],"title":"ChatError","type":"object"};

function validate98(data, {instancePath="", parentData, parentDataProperty, rootData=data, dynamicAnchors={}}={}){
let vErrors = null;
let errors = 0;
const evaluated0 = validate98.evaluated;
if(evaluated0.dynamicProps){
evaluated0.props = undefined;
}
if(evaluated0.dynamicItems){
evaluated0.items = undefined;
}
if(errors === 0){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing0;
if(((data.code === undefined) && (missing0 = "code")) || ((data.message === undefined) && (missing0 = "message"))){
validate98.errors = [{instancePath,schemaPath:"#/required",keyword:"required",params:{missingProperty: missing0},message:"must have required property '"+missing0+"'"}];
return false;
}
else {
const _errs1 = errors;
for(const key0 in data){
if(!((key0 === "code") || (key0 === "message"))){
validate98.errors = [{instancePath,schemaPath:"#/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key0},message:"must NOT have additional properties"}];
return false;
break;
}
}
if(_errs1 === errors){
if(data.code !== undefined){
const _errs2 = errors;
if(typeof data.code !== "string"){
validate98.errors = [{instancePath:instancePath+"/code",schemaPath:"#/properties/code/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs2 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.message !== undefined){
const _errs4 = errors;
if(typeof data.message !== "string"){
validate98.errors = [{instancePath:instancePath+"/message",schemaPath:"#/properties/message/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs4 === errors;
}
else {
var valid0 = true;
}
}
}
}
}
else {
validate98.errors = [{instancePath,schemaPath:"#/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
validate98.errors = vErrors;
return errors === 0;
}
validate98.evaluated = {"props":true,"dynamicProps":false,"dynamicItems":false};

export const identify_args = validate99;
const schema107 = {"$schema":"https://json-schema.org/draft/2020-12/schema","additionalProperties":false,"title":"ChatIdentifyArgs","type":"object"};

function validate99(data, {instancePath="", parentData, parentDataProperty, rootData=data, dynamicAnchors={}}={}){
let vErrors = null;
let errors = 0;
const evaluated0 = validate99.evaluated;
if(evaluated0.dynamicProps){
evaluated0.props = undefined;
}
if(evaluated0.dynamicItems){
evaluated0.items = undefined;
}
if(errors === 0){
if(data && typeof data == "object" && !Array.isArray(data)){
for(const key0 in data){
validate99.errors = [{instancePath,schemaPath:"#/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key0},message:"must NOT have additional properties"}];
return false;
break;
}
}
else {
validate99.errors = [{instancePath,schemaPath:"#/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
validate99.errors = vErrors;
return errors === 0;
}
validate99.evaluated = {"props":true,"dynamicProps":false,"dynamicItems":false};

export const identify_output = validate100;
const schema108 = {"$schema":"https://json-schema.org/draft/2020-12/schema","properties":{"archiveExists":{"type":"boolean"},"bootId":{"type":"string"},"capabilities":{"items":{"type":"string"},"type":"array"},"id":{"type":"string"},"label":{"type":"string"},"locked":{"type":"boolean"},"profileExists":{"type":"boolean"},"protocolLocked":{"type":"boolean"},"safetyNumber":{"type":"string"}},"required":["id","label","bootId","locked","protocolLocked","profileExists","archiveExists","safetyNumber","capabilities"],"title":"InstanceInfo","type":"object"};

function validate100(data, {instancePath="", parentData, parentDataProperty, rootData=data, dynamicAnchors={}}={}){
let vErrors = null;
let errors = 0;
const evaluated0 = validate100.evaluated;
if(evaluated0.dynamicProps){
evaluated0.props = undefined;
}
if(evaluated0.dynamicItems){
evaluated0.items = undefined;
}
if(errors === 0){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing0;
if((((((((((data.id === undefined) && (missing0 = "id")) || ((data.label === undefined) && (missing0 = "label"))) || ((data.bootId === undefined) && (missing0 = "bootId"))) || ((data.locked === undefined) && (missing0 = "locked"))) || ((data.protocolLocked === undefined) && (missing0 = "protocolLocked"))) || ((data.profileExists === undefined) && (missing0 = "profileExists"))) || ((data.archiveExists === undefined) && (missing0 = "archiveExists"))) || ((data.safetyNumber === undefined) && (missing0 = "safetyNumber"))) || ((data.capabilities === undefined) && (missing0 = "capabilities"))){
validate100.errors = [{instancePath,schemaPath:"#/required",keyword:"required",params:{missingProperty: missing0},message:"must have required property '"+missing0+"'"}];
return false;
}
else {
if(data.archiveExists !== undefined){
const _errs1 = errors;
if(typeof data.archiveExists !== "boolean"){
validate100.errors = [{instancePath:instancePath+"/archiveExists",schemaPath:"#/properties/archiveExists/type",keyword:"type",params:{type: "boolean"},message:"must be boolean"}];
return false;
}
var valid0 = _errs1 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.bootId !== undefined){
const _errs3 = errors;
if(typeof data.bootId !== "string"){
validate100.errors = [{instancePath:instancePath+"/bootId",schemaPath:"#/properties/bootId/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs3 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.capabilities !== undefined){
let data2 = data.capabilities;
const _errs5 = errors;
if(errors === _errs5){
if(Array.isArray(data2)){
var valid1 = true;
const len0 = data2.length;
for(let i0=0; i0<len0; i0++){
const _errs7 = errors;
if(typeof data2[i0] !== "string"){
validate100.errors = [{instancePath:instancePath+"/capabilities/" + i0,schemaPath:"#/properties/capabilities/items/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid1 = _errs7 === errors;
if(!valid1){
break;
}
}
}
else {
validate100.errors = [{instancePath:instancePath+"/capabilities",schemaPath:"#/properties/capabilities/type",keyword:"type",params:{type: "array"},message:"must be array"}];
return false;
}
}
var valid0 = _errs5 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.id !== undefined){
const _errs9 = errors;
if(typeof data.id !== "string"){
validate100.errors = [{instancePath:instancePath+"/id",schemaPath:"#/properties/id/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs9 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.label !== undefined){
const _errs11 = errors;
if(typeof data.label !== "string"){
validate100.errors = [{instancePath:instancePath+"/label",schemaPath:"#/properties/label/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs11 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.locked !== undefined){
const _errs13 = errors;
if(typeof data.locked !== "boolean"){
validate100.errors = [{instancePath:instancePath+"/locked",schemaPath:"#/properties/locked/type",keyword:"type",params:{type: "boolean"},message:"must be boolean"}];
return false;
}
var valid0 = _errs13 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.profileExists !== undefined){
const _errs15 = errors;
if(typeof data.profileExists !== "boolean"){
validate100.errors = [{instancePath:instancePath+"/profileExists",schemaPath:"#/properties/profileExists/type",keyword:"type",params:{type: "boolean"},message:"must be boolean"}];
return false;
}
var valid0 = _errs15 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.protocolLocked !== undefined){
const _errs17 = errors;
if(typeof data.protocolLocked !== "boolean"){
validate100.errors = [{instancePath:instancePath+"/protocolLocked",schemaPath:"#/properties/protocolLocked/type",keyword:"type",params:{type: "boolean"},message:"must be boolean"}];
return false;
}
var valid0 = _errs17 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.safetyNumber !== undefined){
const _errs19 = errors;
if(typeof data.safetyNumber !== "string"){
validate100.errors = [{instancePath:instancePath+"/safetyNumber",schemaPath:"#/properties/safetyNumber/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs19 === errors;
}
else {
var valid0 = true;
}
}
}
}
}
}
}
}
}
}
}
else {
validate100.errors = [{instancePath,schemaPath:"#/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
validate100.errors = vErrors;
return errors === 0;
}
validate100.evaluated = {"props":{"archiveExists":true,"bootId":true,"capabilities":true,"id":true,"label":true,"locked":true,"profileExists":true,"protocolLocked":true,"safetyNumber":true},"dynamicProps":false,"dynamicItems":false};

export const identify_error = validate101;
const schema109 = {"$schema":"https://json-schema.org/draft/2020-12/schema","additionalProperties":false,"properties":{"code":{"type":"string"},"message":{"type":"string"}},"required":["code","message"],"title":"ChatError","type":"object"};

function validate101(data, {instancePath="", parentData, parentDataProperty, rootData=data, dynamicAnchors={}}={}){
let vErrors = null;
let errors = 0;
const evaluated0 = validate101.evaluated;
if(evaluated0.dynamicProps){
evaluated0.props = undefined;
}
if(evaluated0.dynamicItems){
evaluated0.items = undefined;
}
if(errors === 0){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing0;
if(((data.code === undefined) && (missing0 = "code")) || ((data.message === undefined) && (missing0 = "message"))){
validate101.errors = [{instancePath,schemaPath:"#/required",keyword:"required",params:{missingProperty: missing0},message:"must have required property '"+missing0+"'"}];
return false;
}
else {
const _errs1 = errors;
for(const key0 in data){
if(!((key0 === "code") || (key0 === "message"))){
validate101.errors = [{instancePath,schemaPath:"#/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key0},message:"must NOT have additional properties"}];
return false;
break;
}
}
if(_errs1 === errors){
if(data.code !== undefined){
const _errs2 = errors;
if(typeof data.code !== "string"){
validate101.errors = [{instancePath:instancePath+"/code",schemaPath:"#/properties/code/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs2 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.message !== undefined){
const _errs4 = errors;
if(typeof data.message !== "string"){
validate101.errors = [{instancePath:instancePath+"/message",schemaPath:"#/properties/message/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs4 === errors;
}
else {
var valid0 = true;
}
}
}
}
}
else {
validate101.errors = [{instancePath,schemaPath:"#/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
validate101.errors = vErrors;
return errors === 0;
}
validate101.evaluated = {"props":true,"dynamicProps":false,"dynamicItems":false};

export const unlock_args = validate102;
const schema110 = {"$schema":"https://json-schema.org/draft/2020-12/schema","additionalProperties":false,"properties":{"create":{"type":"boolean"},"passphrase":{"type":"string"}},"required":["passphrase","create"],"title":"ChatUnlockArgs","type":"object"};

function validate102(data, {instancePath="", parentData, parentDataProperty, rootData=data, dynamicAnchors={}}={}){
let vErrors = null;
let errors = 0;
const evaluated0 = validate102.evaluated;
if(evaluated0.dynamicProps){
evaluated0.props = undefined;
}
if(evaluated0.dynamicItems){
evaluated0.items = undefined;
}
if(errors === 0){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing0;
if(((data.passphrase === undefined) && (missing0 = "passphrase")) || ((data.create === undefined) && (missing0 = "create"))){
validate102.errors = [{instancePath,schemaPath:"#/required",keyword:"required",params:{missingProperty: missing0},message:"must have required property '"+missing0+"'"}];
return false;
}
else {
const _errs1 = errors;
for(const key0 in data){
if(!((key0 === "create") || (key0 === "passphrase"))){
validate102.errors = [{instancePath,schemaPath:"#/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key0},message:"must NOT have additional properties"}];
return false;
break;
}
}
if(_errs1 === errors){
if(data.create !== undefined){
const _errs2 = errors;
if(typeof data.create !== "boolean"){
validate102.errors = [{instancePath:instancePath+"/create",schemaPath:"#/properties/create/type",keyword:"type",params:{type: "boolean"},message:"must be boolean"}];
return false;
}
var valid0 = _errs2 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.passphrase !== undefined){
const _errs4 = errors;
if(typeof data.passphrase !== "string"){
validate102.errors = [{instancePath:instancePath+"/passphrase",schemaPath:"#/properties/passphrase/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs4 === errors;
}
else {
var valid0 = true;
}
}
}
}
}
else {
validate102.errors = [{instancePath,schemaPath:"#/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
validate102.errors = vErrors;
return errors === 0;
}
validate102.evaluated = {"props":true,"dynamicProps":false,"dynamicItems":false};

export const unlock_output = validate103;
const schema111 = {"$defs":{"Activity":{"description":"Authenticated state changes observed by this profile, retained before publication.","properties":{"conversation":{"type":"string"},"id":{"type":"string"},"kind":{"type":"string"},"text":{"type":"string"},"timestamp":{"format":"uint64","minimum":0,"type":"integer"}},"required":["id","conversation","kind","text","timestamp"],"type":"object"},"CommandOutput":{"oneOf":[{"properties":{"commands":{"items":{"$ref":"#/$defs/CommandSpec"},"type":"array"},"kind":{"const":"help","type":"string"}},"required":["kind","commands"],"type":"object"},{"properties":{"channels":{"items":{"$ref":"#/$defs/DirectoryEntry"},"type":"array"},"kind":{"const":"directory","type":"string"}},"required":["kind","channels"],"type":"object"},{"properties":{"channel":{"type":"string"},"expires":{"format":"uint64","minimum":0,"type":"integer"},"kind":{"const":"invitation","type":"string"},"link":{"type":"string"},"localOnly":{"default":false,"type":"boolean"}},"required":["kind","channel","link","expires"],"type":"object"},{"properties":{"kind":{"const":"text","type":"string"},"text":{"type":"string"},"title":{"type":"string"}},"required":["kind","title","text"],"type":"object"},{"properties":{"kind":{"const":"status","type":"string"},"text":{"type":"string"}},"required":["kind","text"],"type":"object"},{"properties":{"conversation":{"type":"string"},"kind":{"const":"close","type":"string"}},"required":["kind","conversation"],"type":"object"}]},"CommandSpec":{"properties":{"available":{"type":"boolean"},"capability":{"type":["string","null"]},"description":{"type":"string"},"name":{"type":"string"},"scope":{"type":"string"},"usage":{"type":"string"}},"required":["name","usage","description","scope","available"],"type":"object"},"Conversation":{"properties":{"active":{"type":"boolean"},"channelId":{"type":"string"},"commands":{"default":[],"items":{"$ref":"#/$defs/CommandSpec"},"type":"array"},"directory":{"default":null,"type":["string","null"]},"id":{"type":"string"},"inputLimitBytes":{"default":12000,"format":"uint","minimum":0,"type":"integer"},"kind":{"$ref":"#/$defs/ConversationKind"},"lastMessageId":{"type":["string","null"]},"members":{"items":{"$ref":"#/$defs/Member"},"type":"array"},"name":{"type":"string"},"owner":{"type":"boolean"},"provider":{"default":null,"type":["string","null"]},"topic":{"type":"string"},"unread":{"format":"uint32","minimum":0,"type":"integer"},"visibility":{"default":null,"type":["string","null"]}},"required":["id","channelId","kind","name","topic","active","owner","members","unread"],"type":"object"},"ConversationKind":{"enum":["channel","query","archive"],"type":"string"},"DirectoryEntry":{"properties":{"conversation":{"type":["string","null"]},"joined":{"type":"boolean"},"name":{"type":"string"}},"required":["name","joined"],"type":"object"},"InputHistoryEntry":{"properties":{"conversation":{"type":["string","null"]},"text":{"type":"string"}},"required":["text"],"type":"object"},"InstanceInfo":{"properties":{"archiveExists":{"type":"boolean"},"bootId":{"type":"string"},"capabilities":{"items":{"type":"string"},"type":"array"},"id":{"type":"string"},"label":{"type":"string"},"locked":{"type":"boolean"},"profileExists":{"type":"boolean"},"protocolLocked":{"type":"boolean"},"safetyNumber":{"type":"string"}},"required":["id","label","bootId","locked","protocolLocked","profileExists","archiveExists","safetyNumber","capabilities"],"type":"object"},"Member":{"properties":{"capabilities":{"default":[],"items":{"type":"string"},"type":"array"},"id":{"type":"string"},"isSelf":{"type":"boolean"},"nickname":{"type":"string"},"recentlyActive":{"default":null,"type":["boolean","null"]}},"required":["id","nickname","isSelf"],"type":"object"},"OperationDetail":{"description":"Safe metadata plus the protected result retained in the encrypted operation journal.","properties":{"action":{"type":"string"},"conversation":{"type":["string","null"]},"id":{"type":"string"},"instance":{"type":"string"},"message":{"type":["string","null"]},"network":{"default":null,"type":["string","null"]},"output":{"anyOf":[{"$ref":"#/$defs/CommandOutput"},{"type":"null"}]},"started":{"format":"uint64","minimum":0,"type":"integer"},"state":{"type":"string"}},"required":["id","instance","action","started","state"],"type":"object"},"ProviderStatus":{"properties":{"code":{"type":"string"},"id":{"type":"string"},"message":{"type":"string"},"retryable":{"type":"boolean"}},"required":["id","code","message","retryable"],"type":"object"}},"$schema":"https://json-schema.org/draft/2020-12/schema","properties":{"activity":{"default":null,"items":{"$ref":"#/$defs/Activity"},"type":["array","null"]},"commandHistory":{"items":{"type":"string"},"type":"array"},"conversations":{"items":{"$ref":"#/$defs/Conversation"},"type":"array"},"inputHistory":{"items":{"$ref":"#/$defs/InputHistoryEntry"},"type":"array"},"instance":{"$ref":"#/$defs/InstanceInfo"},"operations":{"default":null,"items":{"$ref":"#/$defs/OperationDetail"},"type":["array","null"]},"presenceEnabled":{"default":null,"type":["boolean","null"]},"providerErrors":{"default":[],"items":{"$ref":"#/$defs/ProviderStatus"},"type":"array"},"revision":{"type":"string"}},"required":["instance","revision","conversations","commandHistory","inputHistory"],"title":"Snapshot","type":"object"};
const schema112 = {"description":"Authenticated state changes observed by this profile, retained before publication.","properties":{"conversation":{"type":"string"},"id":{"type":"string"},"kind":{"type":"string"},"text":{"type":"string"},"timestamp":{"format":"uint64","minimum":0,"type":"integer"}},"required":["id","conversation","kind","text","timestamp"],"type":"object"};
const schema117 = {"properties":{"conversation":{"type":["string","null"]},"text":{"type":"string"}},"required":["text"],"type":"object"};
const schema118 = {"properties":{"archiveExists":{"type":"boolean"},"bootId":{"type":"string"},"capabilities":{"items":{"type":"string"},"type":"array"},"id":{"type":"string"},"label":{"type":"string"},"locked":{"type":"boolean"},"profileExists":{"type":"boolean"},"protocolLocked":{"type":"boolean"},"safetyNumber":{"type":"string"}},"required":["id","label","bootId","locked","protocolLocked","profileExists","archiveExists","safetyNumber","capabilities"],"type":"object"};
const schema123 = {"properties":{"code":{"type":"string"},"id":{"type":"string"},"message":{"type":"string"},"retryable":{"type":"boolean"}},"required":["id","code","message","retryable"],"type":"object"};
const schema113 = {"properties":{"active":{"type":"boolean"},"channelId":{"type":"string"},"commands":{"default":[],"items":{"$ref":"#/$defs/CommandSpec"},"type":"array"},"directory":{"default":null,"type":["string","null"]},"id":{"type":"string"},"inputLimitBytes":{"default":12000,"format":"uint","minimum":0,"type":"integer"},"kind":{"$ref":"#/$defs/ConversationKind"},"lastMessageId":{"type":["string","null"]},"members":{"items":{"$ref":"#/$defs/Member"},"type":"array"},"name":{"type":"string"},"owner":{"type":"boolean"},"provider":{"default":null,"type":["string","null"]},"topic":{"type":"string"},"unread":{"format":"uint32","minimum":0,"type":"integer"},"visibility":{"default":null,"type":["string","null"]}},"required":["id","channelId","kind","name","topic","active","owner","members","unread"],"type":"object"};
const schema114 = {"properties":{"available":{"type":"boolean"},"capability":{"type":["string","null"]},"description":{"type":"string"},"name":{"type":"string"},"scope":{"type":"string"},"usage":{"type":"string"}},"required":["name","usage","description","scope","available"],"type":"object"};
const schema115 = {"enum":["channel","query","archive"],"type":"string"};
const schema116 = {"properties":{"capabilities":{"default":[],"items":{"type":"string"},"type":"array"},"id":{"type":"string"},"isSelf":{"type":"boolean"},"nickname":{"type":"string"},"recentlyActive":{"default":null,"type":["boolean","null"]}},"required":["id","nickname","isSelf"],"type":"object"};

function validate104(data, {instancePath="", parentData, parentDataProperty, rootData=data, dynamicAnchors={}}={}){
let vErrors = null;
let errors = 0;
const evaluated0 = validate104.evaluated;
if(evaluated0.dynamicProps){
evaluated0.props = undefined;
}
if(evaluated0.dynamicItems){
evaluated0.items = undefined;
}
if(errors === 0){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing0;
if((((((((((data.id === undefined) && (missing0 = "id")) || ((data.channelId === undefined) && (missing0 = "channelId"))) || ((data.kind === undefined) && (missing0 = "kind"))) || ((data.name === undefined) && (missing0 = "name"))) || ((data.topic === undefined) && (missing0 = "topic"))) || ((data.active === undefined) && (missing0 = "active"))) || ((data.owner === undefined) && (missing0 = "owner"))) || ((data.members === undefined) && (missing0 = "members"))) || ((data.unread === undefined) && (missing0 = "unread"))){
validate104.errors = [{instancePath,schemaPath:"#/required",keyword:"required",params:{missingProperty: missing0},message:"must have required property '"+missing0+"'"}];
return false;
}
else {
if(data.active !== undefined){
const _errs1 = errors;
if(typeof data.active !== "boolean"){
validate104.errors = [{instancePath:instancePath+"/active",schemaPath:"#/properties/active/type",keyword:"type",params:{type: "boolean"},message:"must be boolean"}];
return false;
}
var valid0 = _errs1 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.channelId !== undefined){
const _errs3 = errors;
if(typeof data.channelId !== "string"){
validate104.errors = [{instancePath:instancePath+"/channelId",schemaPath:"#/properties/channelId/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs3 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.commands !== undefined){
let data2 = data.commands;
const _errs5 = errors;
if(errors === _errs5){
if(Array.isArray(data2)){
var valid1 = true;
const len0 = data2.length;
for(let i0=0; i0<len0; i0++){
let data3 = data2[i0];
const _errs7 = errors;
const _errs8 = errors;
if(errors === _errs8){
if(data3 && typeof data3 == "object" && !Array.isArray(data3)){
let missing1;
if((((((data3.name === undefined) && (missing1 = "name")) || ((data3.usage === undefined) && (missing1 = "usage"))) || ((data3.description === undefined) && (missing1 = "description"))) || ((data3.scope === undefined) && (missing1 = "scope"))) || ((data3.available === undefined) && (missing1 = "available"))){
validate104.errors = [{instancePath:instancePath+"/commands/" + i0,schemaPath:"#/$defs/CommandSpec/required",keyword:"required",params:{missingProperty: missing1},message:"must have required property '"+missing1+"'"}];
return false;
}
else {
if(data3.available !== undefined){
const _errs10 = errors;
if(typeof data3.available !== "boolean"){
validate104.errors = [{instancePath:instancePath+"/commands/" + i0+"/available",schemaPath:"#/$defs/CommandSpec/properties/available/type",keyword:"type",params:{type: "boolean"},message:"must be boolean"}];
return false;
}
var valid3 = _errs10 === errors;
}
else {
var valid3 = true;
}
if(valid3){
if(data3.capability !== undefined){
let data5 = data3.capability;
const _errs12 = errors;
if((typeof data5 !== "string") && (data5 !== null)){
validate104.errors = [{instancePath:instancePath+"/commands/" + i0+"/capability",schemaPath:"#/$defs/CommandSpec/properties/capability/type",keyword:"type",params:{type: schema114.properties.capability.type},message:"must be string,null"}];
return false;
}
var valid3 = _errs12 === errors;
}
else {
var valid3 = true;
}
if(valid3){
if(data3.description !== undefined){
const _errs14 = errors;
if(typeof data3.description !== "string"){
validate104.errors = [{instancePath:instancePath+"/commands/" + i0+"/description",schemaPath:"#/$defs/CommandSpec/properties/description/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid3 = _errs14 === errors;
}
else {
var valid3 = true;
}
if(valid3){
if(data3.name !== undefined){
const _errs16 = errors;
if(typeof data3.name !== "string"){
validate104.errors = [{instancePath:instancePath+"/commands/" + i0+"/name",schemaPath:"#/$defs/CommandSpec/properties/name/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid3 = _errs16 === errors;
}
else {
var valid3 = true;
}
if(valid3){
if(data3.scope !== undefined){
const _errs18 = errors;
if(typeof data3.scope !== "string"){
validate104.errors = [{instancePath:instancePath+"/commands/" + i0+"/scope",schemaPath:"#/$defs/CommandSpec/properties/scope/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid3 = _errs18 === errors;
}
else {
var valid3 = true;
}
if(valid3){
if(data3.usage !== undefined){
const _errs20 = errors;
if(typeof data3.usage !== "string"){
validate104.errors = [{instancePath:instancePath+"/commands/" + i0+"/usage",schemaPath:"#/$defs/CommandSpec/properties/usage/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid3 = _errs20 === errors;
}
else {
var valid3 = true;
}
}
}
}
}
}
}
}
else {
validate104.errors = [{instancePath:instancePath+"/commands/" + i0,schemaPath:"#/$defs/CommandSpec/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
var valid1 = _errs7 === errors;
if(!valid1){
break;
}
}
}
else {
validate104.errors = [{instancePath:instancePath+"/commands",schemaPath:"#/properties/commands/type",keyword:"type",params:{type: "array"},message:"must be array"}];
return false;
}
}
var valid0 = _errs5 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.directory !== undefined){
let data10 = data.directory;
const _errs22 = errors;
if((typeof data10 !== "string") && (data10 !== null)){
validate104.errors = [{instancePath:instancePath+"/directory",schemaPath:"#/properties/directory/type",keyword:"type",params:{type: schema113.properties.directory.type},message:"must be string,null"}];
return false;
}
var valid0 = _errs22 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.id !== undefined){
const _errs24 = errors;
if(typeof data.id !== "string"){
validate104.errors = [{instancePath:instancePath+"/id",schemaPath:"#/properties/id/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs24 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.inputLimitBytes !== undefined){
let data12 = data.inputLimitBytes;
const _errs26 = errors;
if(!(((typeof data12 == "number") && (!(data12 % 1) && !isNaN(data12))) && (isFinite(data12)))){
validate104.errors = [{instancePath:instancePath+"/inputLimitBytes",schemaPath:"#/properties/inputLimitBytes/type",keyword:"type",params:{type: "integer"},message:"must be integer"}];
return false;
}
if(errors === _errs26){
if((typeof data12 == "number") && (isFinite(data12))){
if(data12 < 0 || isNaN(data12)){
validate104.errors = [{instancePath:instancePath+"/inputLimitBytes",schemaPath:"#/properties/inputLimitBytes/minimum",keyword:"minimum",params:{comparison: ">=", limit: 0},message:"must be >= 0"}];
return false;
}
}
}
var valid0 = _errs26 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.kind !== undefined){
let data13 = data.kind;
const _errs28 = errors;
if(typeof data13 !== "string"){
validate104.errors = [{instancePath:instancePath+"/kind",schemaPath:"#/$defs/ConversationKind/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
if(!(((data13 === "channel") || (data13 === "query")) || (data13 === "archive"))){
validate104.errors = [{instancePath:instancePath+"/kind",schemaPath:"#/$defs/ConversationKind/enum",keyword:"enum",params:{allowedValues: schema115.enum},message:"must be equal to one of the allowed values"}];
return false;
}
var valid0 = _errs28 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.lastMessageId !== undefined){
let data14 = data.lastMessageId;
const _errs31 = errors;
if((typeof data14 !== "string") && (data14 !== null)){
validate104.errors = [{instancePath:instancePath+"/lastMessageId",schemaPath:"#/properties/lastMessageId/type",keyword:"type",params:{type: schema113.properties.lastMessageId.type},message:"must be string,null"}];
return false;
}
var valid0 = _errs31 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.members !== undefined){
let data15 = data.members;
const _errs33 = errors;
if(errors === _errs33){
if(Array.isArray(data15)){
var valid5 = true;
const len1 = data15.length;
for(let i1=0; i1<len1; i1++){
let data16 = data15[i1];
const _errs35 = errors;
const _errs36 = errors;
if(errors === _errs36){
if(data16 && typeof data16 == "object" && !Array.isArray(data16)){
let missing2;
if((((data16.id === undefined) && (missing2 = "id")) || ((data16.nickname === undefined) && (missing2 = "nickname"))) || ((data16.isSelf === undefined) && (missing2 = "isSelf"))){
validate104.errors = [{instancePath:instancePath+"/members/" + i1,schemaPath:"#/$defs/Member/required",keyword:"required",params:{missingProperty: missing2},message:"must have required property '"+missing2+"'"}];
return false;
}
else {
if(data16.capabilities !== undefined){
let data17 = data16.capabilities;
const _errs38 = errors;
if(errors === _errs38){
if(Array.isArray(data17)){
var valid8 = true;
const len2 = data17.length;
for(let i2=0; i2<len2; i2++){
const _errs40 = errors;
if(typeof data17[i2] !== "string"){
validate104.errors = [{instancePath:instancePath+"/members/" + i1+"/capabilities/" + i2,schemaPath:"#/$defs/Member/properties/capabilities/items/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid8 = _errs40 === errors;
if(!valid8){
break;
}
}
}
else {
validate104.errors = [{instancePath:instancePath+"/members/" + i1+"/capabilities",schemaPath:"#/$defs/Member/properties/capabilities/type",keyword:"type",params:{type: "array"},message:"must be array"}];
return false;
}
}
var valid7 = _errs38 === errors;
}
else {
var valid7 = true;
}
if(valid7){
if(data16.id !== undefined){
const _errs42 = errors;
if(typeof data16.id !== "string"){
validate104.errors = [{instancePath:instancePath+"/members/" + i1+"/id",schemaPath:"#/$defs/Member/properties/id/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid7 = _errs42 === errors;
}
else {
var valid7 = true;
}
if(valid7){
if(data16.isSelf !== undefined){
const _errs44 = errors;
if(typeof data16.isSelf !== "boolean"){
validate104.errors = [{instancePath:instancePath+"/members/" + i1+"/isSelf",schemaPath:"#/$defs/Member/properties/isSelf/type",keyword:"type",params:{type: "boolean"},message:"must be boolean"}];
return false;
}
var valid7 = _errs44 === errors;
}
else {
var valid7 = true;
}
if(valid7){
if(data16.nickname !== undefined){
const _errs46 = errors;
if(typeof data16.nickname !== "string"){
validate104.errors = [{instancePath:instancePath+"/members/" + i1+"/nickname",schemaPath:"#/$defs/Member/properties/nickname/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid7 = _errs46 === errors;
}
else {
var valid7 = true;
}
if(valid7){
if(data16.recentlyActive !== undefined){
let data22 = data16.recentlyActive;
const _errs48 = errors;
if((typeof data22 !== "boolean") && (data22 !== null)){
validate104.errors = [{instancePath:instancePath+"/members/" + i1+"/recentlyActive",schemaPath:"#/$defs/Member/properties/recentlyActive/type",keyword:"type",params:{type: schema116.properties.recentlyActive.type},message:"must be boolean,null"}];
return false;
}
var valid7 = _errs48 === errors;
}
else {
var valid7 = true;
}
}
}
}
}
}
}
else {
validate104.errors = [{instancePath:instancePath+"/members/" + i1,schemaPath:"#/$defs/Member/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
var valid5 = _errs35 === errors;
if(!valid5){
break;
}
}
}
else {
validate104.errors = [{instancePath:instancePath+"/members",schemaPath:"#/properties/members/type",keyword:"type",params:{type: "array"},message:"must be array"}];
return false;
}
}
var valid0 = _errs33 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.name !== undefined){
const _errs50 = errors;
if(typeof data.name !== "string"){
validate104.errors = [{instancePath:instancePath+"/name",schemaPath:"#/properties/name/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs50 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.owner !== undefined){
const _errs52 = errors;
if(typeof data.owner !== "boolean"){
validate104.errors = [{instancePath:instancePath+"/owner",schemaPath:"#/properties/owner/type",keyword:"type",params:{type: "boolean"},message:"must be boolean"}];
return false;
}
var valid0 = _errs52 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.provider !== undefined){
let data25 = data.provider;
const _errs54 = errors;
if((typeof data25 !== "string") && (data25 !== null)){
validate104.errors = [{instancePath:instancePath+"/provider",schemaPath:"#/properties/provider/type",keyword:"type",params:{type: schema113.properties.provider.type},message:"must be string,null"}];
return false;
}
var valid0 = _errs54 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.topic !== undefined){
const _errs56 = errors;
if(typeof data.topic !== "string"){
validate104.errors = [{instancePath:instancePath+"/topic",schemaPath:"#/properties/topic/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs56 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.unread !== undefined){
let data27 = data.unread;
const _errs58 = errors;
if(!(((typeof data27 == "number") && (!(data27 % 1) && !isNaN(data27))) && (isFinite(data27)))){
validate104.errors = [{instancePath:instancePath+"/unread",schemaPath:"#/properties/unread/type",keyword:"type",params:{type: "integer"},message:"must be integer"}];
return false;
}
if(errors === _errs58){
if((typeof data27 == "number") && (isFinite(data27))){
if(data27 < 0 || isNaN(data27)){
validate104.errors = [{instancePath:instancePath+"/unread",schemaPath:"#/properties/unread/minimum",keyword:"minimum",params:{comparison: ">=", limit: 0},message:"must be >= 0"}];
return false;
}
}
}
var valid0 = _errs58 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.visibility !== undefined){
let data28 = data.visibility;
const _errs60 = errors;
if((typeof data28 !== "string") && (data28 !== null)){
validate104.errors = [{instancePath:instancePath+"/visibility",schemaPath:"#/properties/visibility/type",keyword:"type",params:{type: schema113.properties.visibility.type},message:"must be string,null"}];
return false;
}
var valid0 = _errs60 === errors;
}
else {
var valid0 = true;
}
}
}
}
}
}
}
}
}
}
}
}
}
}
}
}
}
else {
validate104.errors = [{instancePath,schemaPath:"#/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
validate104.errors = vErrors;
return errors === 0;
}
validate104.evaluated = {"props":{"active":true,"channelId":true,"commands":true,"directory":true,"id":true,"inputLimitBytes":true,"kind":true,"lastMessageId":true,"members":true,"name":true,"owner":true,"provider":true,"topic":true,"unread":true,"visibility":true},"dynamicProps":false,"dynamicItems":false};

const schema119 = {"description":"Safe metadata plus the protected result retained in the encrypted operation journal.","properties":{"action":{"type":"string"},"conversation":{"type":["string","null"]},"id":{"type":"string"},"instance":{"type":"string"},"message":{"type":["string","null"]},"network":{"default":null,"type":["string","null"]},"output":{"anyOf":[{"$ref":"#/$defs/CommandOutput"},{"type":"null"}]},"started":{"format":"uint64","minimum":0,"type":"integer"},"state":{"type":"string"}},"required":["id","instance","action","started","state"],"type":"object"};
const schema120 = {"oneOf":[{"properties":{"commands":{"items":{"$ref":"#/$defs/CommandSpec"},"type":"array"},"kind":{"const":"help","type":"string"}},"required":["kind","commands"],"type":"object"},{"properties":{"channels":{"items":{"$ref":"#/$defs/DirectoryEntry"},"type":"array"},"kind":{"const":"directory","type":"string"}},"required":["kind","channels"],"type":"object"},{"properties":{"channel":{"type":"string"},"expires":{"format":"uint64","minimum":0,"type":"integer"},"kind":{"const":"invitation","type":"string"},"link":{"type":"string"},"localOnly":{"default":false,"type":"boolean"}},"required":["kind","channel","link","expires"],"type":"object"},{"properties":{"kind":{"const":"text","type":"string"},"text":{"type":"string"},"title":{"type":"string"}},"required":["kind","title","text"],"type":"object"},{"properties":{"kind":{"const":"status","type":"string"},"text":{"type":"string"}},"required":["kind","text"],"type":"object"},{"properties":{"conversation":{"type":"string"},"kind":{"const":"close","type":"string"}},"required":["kind","conversation"],"type":"object"}]};
const schema122 = {"properties":{"conversation":{"type":["string","null"]},"joined":{"type":"boolean"},"name":{"type":"string"}},"required":["name","joined"],"type":"object"};

function validate107(data, {instancePath="", parentData, parentDataProperty, rootData=data, dynamicAnchors={}}={}){
let vErrors = null;
let errors = 0;
const evaluated0 = validate107.evaluated;
if(evaluated0.dynamicProps){
evaluated0.props = undefined;
}
if(evaluated0.dynamicItems){
evaluated0.items = undefined;
}
const _errs0 = errors;
let valid0 = false;
let passing0 = null;
const _errs1 = errors;
if(errors === _errs1){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing0;
if(((data.kind === undefined) && (missing0 = "kind")) || ((data.commands === undefined) && (missing0 = "commands"))){
const err0 = {instancePath,schemaPath:"#/oneOf/0/required",keyword:"required",params:{missingProperty: missing0},message:"must have required property '"+missing0+"'"};
if(vErrors === null){
vErrors = [err0];
}
else {
vErrors.push(err0);
}
errors++;
}
else {
if(data.commands !== undefined){
let data0 = data.commands;
const _errs3 = errors;
if(errors === _errs3){
if(Array.isArray(data0)){
var valid2 = true;
const len0 = data0.length;
for(let i0=0; i0<len0; i0++){
let data1 = data0[i0];
const _errs5 = errors;
const _errs6 = errors;
if(errors === _errs6){
if(data1 && typeof data1 == "object" && !Array.isArray(data1)){
let missing1;
if((((((data1.name === undefined) && (missing1 = "name")) || ((data1.usage === undefined) && (missing1 = "usage"))) || ((data1.description === undefined) && (missing1 = "description"))) || ((data1.scope === undefined) && (missing1 = "scope"))) || ((data1.available === undefined) && (missing1 = "available"))){
const err1 = {instancePath:instancePath+"/commands/" + i0,schemaPath:"#/$defs/CommandSpec/required",keyword:"required",params:{missingProperty: missing1},message:"must have required property '"+missing1+"'"};
if(vErrors === null){
vErrors = [err1];
}
else {
vErrors.push(err1);
}
errors++;
}
else {
if(data1.available !== undefined){
const _errs8 = errors;
if(typeof data1.available !== "boolean"){
const err2 = {instancePath:instancePath+"/commands/" + i0+"/available",schemaPath:"#/$defs/CommandSpec/properties/available/type",keyword:"type",params:{type: "boolean"},message:"must be boolean"};
if(vErrors === null){
vErrors = [err2];
}
else {
vErrors.push(err2);
}
errors++;
}
var valid4 = _errs8 === errors;
}
else {
var valid4 = true;
}
if(valid4){
if(data1.capability !== undefined){
let data3 = data1.capability;
const _errs10 = errors;
if((typeof data3 !== "string") && (data3 !== null)){
const err3 = {instancePath:instancePath+"/commands/" + i0+"/capability",schemaPath:"#/$defs/CommandSpec/properties/capability/type",keyword:"type",params:{type: schema114.properties.capability.type},message:"must be string,null"};
if(vErrors === null){
vErrors = [err3];
}
else {
vErrors.push(err3);
}
errors++;
}
var valid4 = _errs10 === errors;
}
else {
var valid4 = true;
}
if(valid4){
if(data1.description !== undefined){
const _errs12 = errors;
if(typeof data1.description !== "string"){
const err4 = {instancePath:instancePath+"/commands/" + i0+"/description",schemaPath:"#/$defs/CommandSpec/properties/description/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err4];
}
else {
vErrors.push(err4);
}
errors++;
}
var valid4 = _errs12 === errors;
}
else {
var valid4 = true;
}
if(valid4){
if(data1.name !== undefined){
const _errs14 = errors;
if(typeof data1.name !== "string"){
const err5 = {instancePath:instancePath+"/commands/" + i0+"/name",schemaPath:"#/$defs/CommandSpec/properties/name/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err5];
}
else {
vErrors.push(err5);
}
errors++;
}
var valid4 = _errs14 === errors;
}
else {
var valid4 = true;
}
if(valid4){
if(data1.scope !== undefined){
const _errs16 = errors;
if(typeof data1.scope !== "string"){
const err6 = {instancePath:instancePath+"/commands/" + i0+"/scope",schemaPath:"#/$defs/CommandSpec/properties/scope/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err6];
}
else {
vErrors.push(err6);
}
errors++;
}
var valid4 = _errs16 === errors;
}
else {
var valid4 = true;
}
if(valid4){
if(data1.usage !== undefined){
const _errs18 = errors;
if(typeof data1.usage !== "string"){
const err7 = {instancePath:instancePath+"/commands/" + i0+"/usage",schemaPath:"#/$defs/CommandSpec/properties/usage/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err7];
}
else {
vErrors.push(err7);
}
errors++;
}
var valid4 = _errs18 === errors;
}
else {
var valid4 = true;
}
}
}
}
}
}
}
}
else {
const err8 = {instancePath:instancePath+"/commands/" + i0,schemaPath:"#/$defs/CommandSpec/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err8];
}
else {
vErrors.push(err8);
}
errors++;
}
}
var valid2 = _errs5 === errors;
if(!valid2){
break;
}
}
}
else {
const err9 = {instancePath:instancePath+"/commands",schemaPath:"#/oneOf/0/properties/commands/type",keyword:"type",params:{type: "array"},message:"must be array"};
if(vErrors === null){
vErrors = [err9];
}
else {
vErrors.push(err9);
}
errors++;
}
}
var valid1 = _errs3 === errors;
}
else {
var valid1 = true;
}
if(valid1){
if(data.kind !== undefined){
let data8 = data.kind;
const _errs20 = errors;
if(typeof data8 !== "string"){
const err10 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/0/properties/kind/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err10];
}
else {
vErrors.push(err10);
}
errors++;
}
if("help" !== data8){
const err11 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/0/properties/kind/const",keyword:"const",params:{allowedValue: "help"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err11];
}
else {
vErrors.push(err11);
}
errors++;
}
var valid1 = _errs20 === errors;
}
else {
var valid1 = true;
}
}
}
}
else {
const err12 = {instancePath,schemaPath:"#/oneOf/0/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err12];
}
else {
vErrors.push(err12);
}
errors++;
}
}
var _valid0 = _errs1 === errors;
if(_valid0){
valid0 = true;
passing0 = 0;
var props0 = {};
props0.commands = true;
props0.kind = true;
}
const _errs22 = errors;
if(errors === _errs22){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing2;
if(((data.kind === undefined) && (missing2 = "kind")) || ((data.channels === undefined) && (missing2 = "channels"))){
const err13 = {instancePath,schemaPath:"#/oneOf/1/required",keyword:"required",params:{missingProperty: missing2},message:"must have required property '"+missing2+"'"};
if(vErrors === null){
vErrors = [err13];
}
else {
vErrors.push(err13);
}
errors++;
}
else {
if(data.channels !== undefined){
let data9 = data.channels;
const _errs24 = errors;
if(errors === _errs24){
if(Array.isArray(data9)){
var valid6 = true;
const len1 = data9.length;
for(let i1=0; i1<len1; i1++){
let data10 = data9[i1];
const _errs26 = errors;
const _errs27 = errors;
if(errors === _errs27){
if(data10 && typeof data10 == "object" && !Array.isArray(data10)){
let missing3;
if(((data10.name === undefined) && (missing3 = "name")) || ((data10.joined === undefined) && (missing3 = "joined"))){
const err14 = {instancePath:instancePath+"/channels/" + i1,schemaPath:"#/$defs/DirectoryEntry/required",keyword:"required",params:{missingProperty: missing3},message:"must have required property '"+missing3+"'"};
if(vErrors === null){
vErrors = [err14];
}
else {
vErrors.push(err14);
}
errors++;
}
else {
if(data10.conversation !== undefined){
let data11 = data10.conversation;
const _errs29 = errors;
if((typeof data11 !== "string") && (data11 !== null)){
const err15 = {instancePath:instancePath+"/channels/" + i1+"/conversation",schemaPath:"#/$defs/DirectoryEntry/properties/conversation/type",keyword:"type",params:{type: schema122.properties.conversation.type},message:"must be string,null"};
if(vErrors === null){
vErrors = [err15];
}
else {
vErrors.push(err15);
}
errors++;
}
var valid8 = _errs29 === errors;
}
else {
var valid8 = true;
}
if(valid8){
if(data10.joined !== undefined){
const _errs31 = errors;
if(typeof data10.joined !== "boolean"){
const err16 = {instancePath:instancePath+"/channels/" + i1+"/joined",schemaPath:"#/$defs/DirectoryEntry/properties/joined/type",keyword:"type",params:{type: "boolean"},message:"must be boolean"};
if(vErrors === null){
vErrors = [err16];
}
else {
vErrors.push(err16);
}
errors++;
}
var valid8 = _errs31 === errors;
}
else {
var valid8 = true;
}
if(valid8){
if(data10.name !== undefined){
const _errs33 = errors;
if(typeof data10.name !== "string"){
const err17 = {instancePath:instancePath+"/channels/" + i1+"/name",schemaPath:"#/$defs/DirectoryEntry/properties/name/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err17];
}
else {
vErrors.push(err17);
}
errors++;
}
var valid8 = _errs33 === errors;
}
else {
var valid8 = true;
}
}
}
}
}
else {
const err18 = {instancePath:instancePath+"/channels/" + i1,schemaPath:"#/$defs/DirectoryEntry/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err18];
}
else {
vErrors.push(err18);
}
errors++;
}
}
var valid6 = _errs26 === errors;
if(!valid6){
break;
}
}
}
else {
const err19 = {instancePath:instancePath+"/channels",schemaPath:"#/oneOf/1/properties/channels/type",keyword:"type",params:{type: "array"},message:"must be array"};
if(vErrors === null){
vErrors = [err19];
}
else {
vErrors.push(err19);
}
errors++;
}
}
var valid5 = _errs24 === errors;
}
else {
var valid5 = true;
}
if(valid5){
if(data.kind !== undefined){
let data14 = data.kind;
const _errs35 = errors;
if(typeof data14 !== "string"){
const err20 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/1/properties/kind/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err20];
}
else {
vErrors.push(err20);
}
errors++;
}
if("directory" !== data14){
const err21 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/1/properties/kind/const",keyword:"const",params:{allowedValue: "directory"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err21];
}
else {
vErrors.push(err21);
}
errors++;
}
var valid5 = _errs35 === errors;
}
else {
var valid5 = true;
}
}
}
}
else {
const err22 = {instancePath,schemaPath:"#/oneOf/1/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err22];
}
else {
vErrors.push(err22);
}
errors++;
}
}
var _valid0 = _errs22 === errors;
if(_valid0 && valid0){
valid0 = false;
passing0 = [passing0, 1];
}
else {
if(_valid0){
valid0 = true;
passing0 = 1;
if(props0 !== true){
props0 = props0 || {};
props0.channels = true;
props0.kind = true;
}
}
const _errs37 = errors;
if(errors === _errs37){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing4;
if(((((data.kind === undefined) && (missing4 = "kind")) || ((data.channel === undefined) && (missing4 = "channel"))) || ((data.link === undefined) && (missing4 = "link"))) || ((data.expires === undefined) && (missing4 = "expires"))){
const err23 = {instancePath,schemaPath:"#/oneOf/2/required",keyword:"required",params:{missingProperty: missing4},message:"must have required property '"+missing4+"'"};
if(vErrors === null){
vErrors = [err23];
}
else {
vErrors.push(err23);
}
errors++;
}
else {
if(data.channel !== undefined){
const _errs39 = errors;
if(typeof data.channel !== "string"){
const err24 = {instancePath:instancePath+"/channel",schemaPath:"#/oneOf/2/properties/channel/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err24];
}
else {
vErrors.push(err24);
}
errors++;
}
var valid9 = _errs39 === errors;
}
else {
var valid9 = true;
}
if(valid9){
if(data.expires !== undefined){
let data16 = data.expires;
const _errs41 = errors;
if(!(((typeof data16 == "number") && (!(data16 % 1) && !isNaN(data16))) && (isFinite(data16)))){
const err25 = {instancePath:instancePath+"/expires",schemaPath:"#/oneOf/2/properties/expires/type",keyword:"type",params:{type: "integer"},message:"must be integer"};
if(vErrors === null){
vErrors = [err25];
}
else {
vErrors.push(err25);
}
errors++;
}
if(errors === _errs41){
if((typeof data16 == "number") && (isFinite(data16))){
if(data16 < 0 || isNaN(data16)){
const err26 = {instancePath:instancePath+"/expires",schemaPath:"#/oneOf/2/properties/expires/minimum",keyword:"minimum",params:{comparison: ">=", limit: 0},message:"must be >= 0"};
if(vErrors === null){
vErrors = [err26];
}
else {
vErrors.push(err26);
}
errors++;
}
}
}
var valid9 = _errs41 === errors;
}
else {
var valid9 = true;
}
if(valid9){
if(data.kind !== undefined){
let data17 = data.kind;
const _errs43 = errors;
if(typeof data17 !== "string"){
const err27 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/2/properties/kind/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err27];
}
else {
vErrors.push(err27);
}
errors++;
}
if("invitation" !== data17){
const err28 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/2/properties/kind/const",keyword:"const",params:{allowedValue: "invitation"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err28];
}
else {
vErrors.push(err28);
}
errors++;
}
var valid9 = _errs43 === errors;
}
else {
var valid9 = true;
}
if(valid9){
if(data.link !== undefined){
const _errs45 = errors;
if(typeof data.link !== "string"){
const err29 = {instancePath:instancePath+"/link",schemaPath:"#/oneOf/2/properties/link/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err29];
}
else {
vErrors.push(err29);
}
errors++;
}
var valid9 = _errs45 === errors;
}
else {
var valid9 = true;
}
if(valid9){
if(data.localOnly !== undefined){
const _errs47 = errors;
if(typeof data.localOnly !== "boolean"){
const err30 = {instancePath:instancePath+"/localOnly",schemaPath:"#/oneOf/2/properties/localOnly/type",keyword:"type",params:{type: "boolean"},message:"must be boolean"};
if(vErrors === null){
vErrors = [err30];
}
else {
vErrors.push(err30);
}
errors++;
}
var valid9 = _errs47 === errors;
}
else {
var valid9 = true;
}
}
}
}
}
}
}
else {
const err31 = {instancePath,schemaPath:"#/oneOf/2/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err31];
}
else {
vErrors.push(err31);
}
errors++;
}
}
var _valid0 = _errs37 === errors;
if(_valid0 && valid0){
valid0 = false;
passing0 = [passing0, 2];
}
else {
if(_valid0){
valid0 = true;
passing0 = 2;
if(props0 !== true){
props0 = props0 || {};
props0.channel = true;
props0.expires = true;
props0.kind = true;
props0.link = true;
props0.localOnly = true;
}
}
const _errs49 = errors;
if(errors === _errs49){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing5;
if((((data.kind === undefined) && (missing5 = "kind")) || ((data.title === undefined) && (missing5 = "title"))) || ((data.text === undefined) && (missing5 = "text"))){
const err32 = {instancePath,schemaPath:"#/oneOf/3/required",keyword:"required",params:{missingProperty: missing5},message:"must have required property '"+missing5+"'"};
if(vErrors === null){
vErrors = [err32];
}
else {
vErrors.push(err32);
}
errors++;
}
else {
if(data.kind !== undefined){
let data20 = data.kind;
const _errs51 = errors;
if(typeof data20 !== "string"){
const err33 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/3/properties/kind/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err33];
}
else {
vErrors.push(err33);
}
errors++;
}
if("text" !== data20){
const err34 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/3/properties/kind/const",keyword:"const",params:{allowedValue: "text"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err34];
}
else {
vErrors.push(err34);
}
errors++;
}
var valid10 = _errs51 === errors;
}
else {
var valid10 = true;
}
if(valid10){
if(data.text !== undefined){
const _errs53 = errors;
if(typeof data.text !== "string"){
const err35 = {instancePath:instancePath+"/text",schemaPath:"#/oneOf/3/properties/text/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err35];
}
else {
vErrors.push(err35);
}
errors++;
}
var valid10 = _errs53 === errors;
}
else {
var valid10 = true;
}
if(valid10){
if(data.title !== undefined){
const _errs55 = errors;
if(typeof data.title !== "string"){
const err36 = {instancePath:instancePath+"/title",schemaPath:"#/oneOf/3/properties/title/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err36];
}
else {
vErrors.push(err36);
}
errors++;
}
var valid10 = _errs55 === errors;
}
else {
var valid10 = true;
}
}
}
}
}
else {
const err37 = {instancePath,schemaPath:"#/oneOf/3/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err37];
}
else {
vErrors.push(err37);
}
errors++;
}
}
var _valid0 = _errs49 === errors;
if(_valid0 && valid0){
valid0 = false;
passing0 = [passing0, 3];
}
else {
if(_valid0){
valid0 = true;
passing0 = 3;
if(props0 !== true){
props0 = props0 || {};
props0.kind = true;
props0.text = true;
props0.title = true;
}
}
const _errs57 = errors;
if(errors === _errs57){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing6;
if(((data.kind === undefined) && (missing6 = "kind")) || ((data.text === undefined) && (missing6 = "text"))){
const err38 = {instancePath,schemaPath:"#/oneOf/4/required",keyword:"required",params:{missingProperty: missing6},message:"must have required property '"+missing6+"'"};
if(vErrors === null){
vErrors = [err38];
}
else {
vErrors.push(err38);
}
errors++;
}
else {
if(data.kind !== undefined){
let data23 = data.kind;
const _errs59 = errors;
if(typeof data23 !== "string"){
const err39 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/4/properties/kind/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err39];
}
else {
vErrors.push(err39);
}
errors++;
}
if("status" !== data23){
const err40 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/4/properties/kind/const",keyword:"const",params:{allowedValue: "status"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err40];
}
else {
vErrors.push(err40);
}
errors++;
}
var valid11 = _errs59 === errors;
}
else {
var valid11 = true;
}
if(valid11){
if(data.text !== undefined){
const _errs61 = errors;
if(typeof data.text !== "string"){
const err41 = {instancePath:instancePath+"/text",schemaPath:"#/oneOf/4/properties/text/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err41];
}
else {
vErrors.push(err41);
}
errors++;
}
var valid11 = _errs61 === errors;
}
else {
var valid11 = true;
}
}
}
}
else {
const err42 = {instancePath,schemaPath:"#/oneOf/4/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err42];
}
else {
vErrors.push(err42);
}
errors++;
}
}
var _valid0 = _errs57 === errors;
if(_valid0 && valid0){
valid0 = false;
passing0 = [passing0, 4];
}
else {
if(_valid0){
valid0 = true;
passing0 = 4;
if(props0 !== true){
props0 = props0 || {};
props0.kind = true;
props0.text = true;
}
}
const _errs63 = errors;
if(errors === _errs63){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing7;
if(((data.kind === undefined) && (missing7 = "kind")) || ((data.conversation === undefined) && (missing7 = "conversation"))){
const err43 = {instancePath,schemaPath:"#/oneOf/5/required",keyword:"required",params:{missingProperty: missing7},message:"must have required property '"+missing7+"'"};
if(vErrors === null){
vErrors = [err43];
}
else {
vErrors.push(err43);
}
errors++;
}
else {
if(data.conversation !== undefined){
const _errs65 = errors;
if(typeof data.conversation !== "string"){
const err44 = {instancePath:instancePath+"/conversation",schemaPath:"#/oneOf/5/properties/conversation/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err44];
}
else {
vErrors.push(err44);
}
errors++;
}
var valid12 = _errs65 === errors;
}
else {
var valid12 = true;
}
if(valid12){
if(data.kind !== undefined){
let data26 = data.kind;
const _errs67 = errors;
if(typeof data26 !== "string"){
const err45 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/5/properties/kind/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err45];
}
else {
vErrors.push(err45);
}
errors++;
}
if("close" !== data26){
const err46 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/5/properties/kind/const",keyword:"const",params:{allowedValue: "close"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err46];
}
else {
vErrors.push(err46);
}
errors++;
}
var valid12 = _errs67 === errors;
}
else {
var valid12 = true;
}
}
}
}
else {
const err47 = {instancePath,schemaPath:"#/oneOf/5/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err47];
}
else {
vErrors.push(err47);
}
errors++;
}
}
var _valid0 = _errs63 === errors;
if(_valid0 && valid0){
valid0 = false;
passing0 = [passing0, 5];
}
else {
if(_valid0){
valid0 = true;
passing0 = 5;
if(props0 !== true){
props0 = props0 || {};
props0.conversation = true;
props0.kind = true;
}
}
}
}
}
}
}
if(!valid0){
const err48 = {instancePath,schemaPath:"#/oneOf",keyword:"oneOf",params:{passingSchemas: passing0},message:"must match exactly one schema in oneOf"};
if(vErrors === null){
vErrors = [err48];
}
else {
vErrors.push(err48);
}
errors++;
validate107.errors = vErrors;
return false;
}
else {
errors = _errs0;
if(vErrors !== null){
if(_errs0){
vErrors.length = _errs0;
}
else {
vErrors = null;
}
}
}
validate107.errors = vErrors;
evaluated0.props = props0;
return errors === 0;
}
validate107.evaluated = {"dynamicProps":true,"dynamicItems":false};


function validate106(data, {instancePath="", parentData, parentDataProperty, rootData=data, dynamicAnchors={}}={}){
let vErrors = null;
let errors = 0;
const evaluated0 = validate106.evaluated;
if(evaluated0.dynamicProps){
evaluated0.props = undefined;
}
if(evaluated0.dynamicItems){
evaluated0.items = undefined;
}
if(errors === 0){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing0;
if((((((data.id === undefined) && (missing0 = "id")) || ((data.instance === undefined) && (missing0 = "instance"))) || ((data.action === undefined) && (missing0 = "action"))) || ((data.started === undefined) && (missing0 = "started"))) || ((data.state === undefined) && (missing0 = "state"))){
validate106.errors = [{instancePath,schemaPath:"#/required",keyword:"required",params:{missingProperty: missing0},message:"must have required property '"+missing0+"'"}];
return false;
}
else {
if(data.action !== undefined){
const _errs1 = errors;
if(typeof data.action !== "string"){
validate106.errors = [{instancePath:instancePath+"/action",schemaPath:"#/properties/action/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs1 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.conversation !== undefined){
let data1 = data.conversation;
const _errs3 = errors;
if((typeof data1 !== "string") && (data1 !== null)){
validate106.errors = [{instancePath:instancePath+"/conversation",schemaPath:"#/properties/conversation/type",keyword:"type",params:{type: schema119.properties.conversation.type},message:"must be string,null"}];
return false;
}
var valid0 = _errs3 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.id !== undefined){
const _errs5 = errors;
if(typeof data.id !== "string"){
validate106.errors = [{instancePath:instancePath+"/id",schemaPath:"#/properties/id/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs5 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.instance !== undefined){
const _errs7 = errors;
if(typeof data.instance !== "string"){
validate106.errors = [{instancePath:instancePath+"/instance",schemaPath:"#/properties/instance/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs7 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.message !== undefined){
let data4 = data.message;
const _errs9 = errors;
if((typeof data4 !== "string") && (data4 !== null)){
validate106.errors = [{instancePath:instancePath+"/message",schemaPath:"#/properties/message/type",keyword:"type",params:{type: schema119.properties.message.type},message:"must be string,null"}];
return false;
}
var valid0 = _errs9 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.network !== undefined){
let data5 = data.network;
const _errs11 = errors;
if((typeof data5 !== "string") && (data5 !== null)){
validate106.errors = [{instancePath:instancePath+"/network",schemaPath:"#/properties/network/type",keyword:"type",params:{type: schema119.properties.network.type},message:"must be string,null"}];
return false;
}
var valid0 = _errs11 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.output !== undefined){
let data6 = data.output;
const _errs13 = errors;
const _errs14 = errors;
let valid1 = false;
const _errs15 = errors;
if(!(validate107(data6, {instancePath:instancePath+"/output",parentData:data,parentDataProperty:"output",rootData,dynamicAnchors}))){
vErrors = vErrors === null ? validate107.errors : vErrors.concat(validate107.errors);
errors = vErrors.length;
}
var _valid0 = _errs15 === errors;
valid1 = valid1 || _valid0;
const _errs16 = errors;
if(data6 !== null){
const err0 = {instancePath:instancePath+"/output",schemaPath:"#/properties/output/anyOf/1/type",keyword:"type",params:{type: "null"},message:"must be null"};
if(vErrors === null){
vErrors = [err0];
}
else {
vErrors.push(err0);
}
errors++;
}
var _valid0 = _errs16 === errors;
valid1 = valid1 || _valid0;
if(!valid1){
const err1 = {instancePath:instancePath+"/output",schemaPath:"#/properties/output/anyOf",keyword:"anyOf",params:{},message:"must match a schema in anyOf"};
if(vErrors === null){
vErrors = [err1];
}
else {
vErrors.push(err1);
}
errors++;
validate106.errors = vErrors;
return false;
}
else {
errors = _errs14;
if(vErrors !== null){
if(_errs14){
vErrors.length = _errs14;
}
else {
vErrors = null;
}
}
}
var valid0 = _errs13 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.started !== undefined){
let data7 = data.started;
const _errs18 = errors;
if(!(((typeof data7 == "number") && (!(data7 % 1) && !isNaN(data7))) && (isFinite(data7)))){
validate106.errors = [{instancePath:instancePath+"/started",schemaPath:"#/properties/started/type",keyword:"type",params:{type: "integer"},message:"must be integer"}];
return false;
}
if(errors === _errs18){
if((typeof data7 == "number") && (isFinite(data7))){
if(data7 < 0 || isNaN(data7)){
validate106.errors = [{instancePath:instancePath+"/started",schemaPath:"#/properties/started/minimum",keyword:"minimum",params:{comparison: ">=", limit: 0},message:"must be >= 0"}];
return false;
}
}
}
var valid0 = _errs18 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.state !== undefined){
const _errs20 = errors;
if(typeof data.state !== "string"){
validate106.errors = [{instancePath:instancePath+"/state",schemaPath:"#/properties/state/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs20 === errors;
}
else {
var valid0 = true;
}
}
}
}
}
}
}
}
}
}
}
else {
validate106.errors = [{instancePath,schemaPath:"#/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
validate106.errors = vErrors;
return errors === 0;
}
validate106.evaluated = {"props":{"action":true,"conversation":true,"id":true,"instance":true,"message":true,"network":true,"output":true,"started":true,"state":true},"dynamicProps":false,"dynamicItems":false};


function validate103(data, {instancePath="", parentData, parentDataProperty, rootData=data, dynamicAnchors={}}={}){
let vErrors = null;
let errors = 0;
const evaluated0 = validate103.evaluated;
if(evaluated0.dynamicProps){
evaluated0.props = undefined;
}
if(evaluated0.dynamicItems){
evaluated0.items = undefined;
}
if(errors === 0){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing0;
if((((((data.instance === undefined) && (missing0 = "instance")) || ((data.revision === undefined) && (missing0 = "revision"))) || ((data.conversations === undefined) && (missing0 = "conversations"))) || ((data.commandHistory === undefined) && (missing0 = "commandHistory"))) || ((data.inputHistory === undefined) && (missing0 = "inputHistory"))){
validate103.errors = [{instancePath,schemaPath:"#/required",keyword:"required",params:{missingProperty: missing0},message:"must have required property '"+missing0+"'"}];
return false;
}
else {
if(data.activity !== undefined){
let data0 = data.activity;
const _errs1 = errors;
if((!(Array.isArray(data0))) && (data0 !== null)){
validate103.errors = [{instancePath:instancePath+"/activity",schemaPath:"#/properties/activity/type",keyword:"type",params:{type: schema111.properties.activity.type},message:"must be array,null"}];
return false;
}
if(errors === _errs1){
if(Array.isArray(data0)){
var valid1 = true;
const len0 = data0.length;
for(let i0=0; i0<len0; i0++){
let data1 = data0[i0];
const _errs3 = errors;
const _errs4 = errors;
if(errors === _errs4){
if(data1 && typeof data1 == "object" && !Array.isArray(data1)){
let missing1;
if((((((data1.id === undefined) && (missing1 = "id")) || ((data1.conversation === undefined) && (missing1 = "conversation"))) || ((data1.kind === undefined) && (missing1 = "kind"))) || ((data1.text === undefined) && (missing1 = "text"))) || ((data1.timestamp === undefined) && (missing1 = "timestamp"))){
validate103.errors = [{instancePath:instancePath+"/activity/" + i0,schemaPath:"#/$defs/Activity/required",keyword:"required",params:{missingProperty: missing1},message:"must have required property '"+missing1+"'"}];
return false;
}
else {
if(data1.conversation !== undefined){
const _errs6 = errors;
if(typeof data1.conversation !== "string"){
validate103.errors = [{instancePath:instancePath+"/activity/" + i0+"/conversation",schemaPath:"#/$defs/Activity/properties/conversation/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid3 = _errs6 === errors;
}
else {
var valid3 = true;
}
if(valid3){
if(data1.id !== undefined){
const _errs8 = errors;
if(typeof data1.id !== "string"){
validate103.errors = [{instancePath:instancePath+"/activity/" + i0+"/id",schemaPath:"#/$defs/Activity/properties/id/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid3 = _errs8 === errors;
}
else {
var valid3 = true;
}
if(valid3){
if(data1.kind !== undefined){
const _errs10 = errors;
if(typeof data1.kind !== "string"){
validate103.errors = [{instancePath:instancePath+"/activity/" + i0+"/kind",schemaPath:"#/$defs/Activity/properties/kind/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid3 = _errs10 === errors;
}
else {
var valid3 = true;
}
if(valid3){
if(data1.text !== undefined){
const _errs12 = errors;
if(typeof data1.text !== "string"){
validate103.errors = [{instancePath:instancePath+"/activity/" + i0+"/text",schemaPath:"#/$defs/Activity/properties/text/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid3 = _errs12 === errors;
}
else {
var valid3 = true;
}
if(valid3){
if(data1.timestamp !== undefined){
let data6 = data1.timestamp;
const _errs14 = errors;
if(!(((typeof data6 == "number") && (!(data6 % 1) && !isNaN(data6))) && (isFinite(data6)))){
validate103.errors = [{instancePath:instancePath+"/activity/" + i0+"/timestamp",schemaPath:"#/$defs/Activity/properties/timestamp/type",keyword:"type",params:{type: "integer"},message:"must be integer"}];
return false;
}
if(errors === _errs14){
if((typeof data6 == "number") && (isFinite(data6))){
if(data6 < 0 || isNaN(data6)){
validate103.errors = [{instancePath:instancePath+"/activity/" + i0+"/timestamp",schemaPath:"#/$defs/Activity/properties/timestamp/minimum",keyword:"minimum",params:{comparison: ">=", limit: 0},message:"must be >= 0"}];
return false;
}
}
}
var valid3 = _errs14 === errors;
}
else {
var valid3 = true;
}
}
}
}
}
}
}
else {
validate103.errors = [{instancePath:instancePath+"/activity/" + i0,schemaPath:"#/$defs/Activity/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
var valid1 = _errs3 === errors;
if(!valid1){
break;
}
}
}
}
var valid0 = _errs1 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.commandHistory !== undefined){
let data7 = data.commandHistory;
const _errs16 = errors;
if(errors === _errs16){
if(Array.isArray(data7)){
var valid4 = true;
const len1 = data7.length;
for(let i1=0; i1<len1; i1++){
const _errs18 = errors;
if(typeof data7[i1] !== "string"){
validate103.errors = [{instancePath:instancePath+"/commandHistory/" + i1,schemaPath:"#/properties/commandHistory/items/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid4 = _errs18 === errors;
if(!valid4){
break;
}
}
}
else {
validate103.errors = [{instancePath:instancePath+"/commandHistory",schemaPath:"#/properties/commandHistory/type",keyword:"type",params:{type: "array"},message:"must be array"}];
return false;
}
}
var valid0 = _errs16 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.conversations !== undefined){
let data9 = data.conversations;
const _errs20 = errors;
if(errors === _errs20){
if(Array.isArray(data9)){
var valid5 = true;
const len2 = data9.length;
for(let i2=0; i2<len2; i2++){
const _errs22 = errors;
if(!(validate104(data9[i2], {instancePath:instancePath+"/conversations/" + i2,parentData:data9,parentDataProperty:i2,rootData,dynamicAnchors}))){
vErrors = vErrors === null ? validate104.errors : vErrors.concat(validate104.errors);
errors = vErrors.length;
}
var valid5 = _errs22 === errors;
if(!valid5){
break;
}
}
}
else {
validate103.errors = [{instancePath:instancePath+"/conversations",schemaPath:"#/properties/conversations/type",keyword:"type",params:{type: "array"},message:"must be array"}];
return false;
}
}
var valid0 = _errs20 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.inputHistory !== undefined){
let data11 = data.inputHistory;
const _errs23 = errors;
if(errors === _errs23){
if(Array.isArray(data11)){
var valid6 = true;
const len3 = data11.length;
for(let i3=0; i3<len3; i3++){
let data12 = data11[i3];
const _errs25 = errors;
const _errs26 = errors;
if(errors === _errs26){
if(data12 && typeof data12 == "object" && !Array.isArray(data12)){
let missing2;
if((data12.text === undefined) && (missing2 = "text")){
validate103.errors = [{instancePath:instancePath+"/inputHistory/" + i3,schemaPath:"#/$defs/InputHistoryEntry/required",keyword:"required",params:{missingProperty: missing2},message:"must have required property '"+missing2+"'"}];
return false;
}
else {
if(data12.conversation !== undefined){
let data13 = data12.conversation;
const _errs28 = errors;
if((typeof data13 !== "string") && (data13 !== null)){
validate103.errors = [{instancePath:instancePath+"/inputHistory/" + i3+"/conversation",schemaPath:"#/$defs/InputHistoryEntry/properties/conversation/type",keyword:"type",params:{type: schema117.properties.conversation.type},message:"must be string,null"}];
return false;
}
var valid8 = _errs28 === errors;
}
else {
var valid8 = true;
}
if(valid8){
if(data12.text !== undefined){
const _errs30 = errors;
if(typeof data12.text !== "string"){
validate103.errors = [{instancePath:instancePath+"/inputHistory/" + i3+"/text",schemaPath:"#/$defs/InputHistoryEntry/properties/text/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid8 = _errs30 === errors;
}
else {
var valid8 = true;
}
}
}
}
else {
validate103.errors = [{instancePath:instancePath+"/inputHistory/" + i3,schemaPath:"#/$defs/InputHistoryEntry/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
var valid6 = _errs25 === errors;
if(!valid6){
break;
}
}
}
else {
validate103.errors = [{instancePath:instancePath+"/inputHistory",schemaPath:"#/properties/inputHistory/type",keyword:"type",params:{type: "array"},message:"must be array"}];
return false;
}
}
var valid0 = _errs23 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.instance !== undefined){
let data15 = data.instance;
const _errs32 = errors;
const _errs33 = errors;
if(errors === _errs33){
if(data15 && typeof data15 == "object" && !Array.isArray(data15)){
let missing3;
if((((((((((data15.id === undefined) && (missing3 = "id")) || ((data15.label === undefined) && (missing3 = "label"))) || ((data15.bootId === undefined) && (missing3 = "bootId"))) || ((data15.locked === undefined) && (missing3 = "locked"))) || ((data15.protocolLocked === undefined) && (missing3 = "protocolLocked"))) || ((data15.profileExists === undefined) && (missing3 = "profileExists"))) || ((data15.archiveExists === undefined) && (missing3 = "archiveExists"))) || ((data15.safetyNumber === undefined) && (missing3 = "safetyNumber"))) || ((data15.capabilities === undefined) && (missing3 = "capabilities"))){
validate103.errors = [{instancePath:instancePath+"/instance",schemaPath:"#/$defs/InstanceInfo/required",keyword:"required",params:{missingProperty: missing3},message:"must have required property '"+missing3+"'"}];
return false;
}
else {
if(data15.archiveExists !== undefined){
const _errs35 = errors;
if(typeof data15.archiveExists !== "boolean"){
validate103.errors = [{instancePath:instancePath+"/instance/archiveExists",schemaPath:"#/$defs/InstanceInfo/properties/archiveExists/type",keyword:"type",params:{type: "boolean"},message:"must be boolean"}];
return false;
}
var valid10 = _errs35 === errors;
}
else {
var valid10 = true;
}
if(valid10){
if(data15.bootId !== undefined){
const _errs37 = errors;
if(typeof data15.bootId !== "string"){
validate103.errors = [{instancePath:instancePath+"/instance/bootId",schemaPath:"#/$defs/InstanceInfo/properties/bootId/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid10 = _errs37 === errors;
}
else {
var valid10 = true;
}
if(valid10){
if(data15.capabilities !== undefined){
let data18 = data15.capabilities;
const _errs39 = errors;
if(errors === _errs39){
if(Array.isArray(data18)){
var valid11 = true;
const len4 = data18.length;
for(let i4=0; i4<len4; i4++){
const _errs41 = errors;
if(typeof data18[i4] !== "string"){
validate103.errors = [{instancePath:instancePath+"/instance/capabilities/" + i4,schemaPath:"#/$defs/InstanceInfo/properties/capabilities/items/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid11 = _errs41 === errors;
if(!valid11){
break;
}
}
}
else {
validate103.errors = [{instancePath:instancePath+"/instance/capabilities",schemaPath:"#/$defs/InstanceInfo/properties/capabilities/type",keyword:"type",params:{type: "array"},message:"must be array"}];
return false;
}
}
var valid10 = _errs39 === errors;
}
else {
var valid10 = true;
}
if(valid10){
if(data15.id !== undefined){
const _errs43 = errors;
if(typeof data15.id !== "string"){
validate103.errors = [{instancePath:instancePath+"/instance/id",schemaPath:"#/$defs/InstanceInfo/properties/id/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid10 = _errs43 === errors;
}
else {
var valid10 = true;
}
if(valid10){
if(data15.label !== undefined){
const _errs45 = errors;
if(typeof data15.label !== "string"){
validate103.errors = [{instancePath:instancePath+"/instance/label",schemaPath:"#/$defs/InstanceInfo/properties/label/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid10 = _errs45 === errors;
}
else {
var valid10 = true;
}
if(valid10){
if(data15.locked !== undefined){
const _errs47 = errors;
if(typeof data15.locked !== "boolean"){
validate103.errors = [{instancePath:instancePath+"/instance/locked",schemaPath:"#/$defs/InstanceInfo/properties/locked/type",keyword:"type",params:{type: "boolean"},message:"must be boolean"}];
return false;
}
var valid10 = _errs47 === errors;
}
else {
var valid10 = true;
}
if(valid10){
if(data15.profileExists !== undefined){
const _errs49 = errors;
if(typeof data15.profileExists !== "boolean"){
validate103.errors = [{instancePath:instancePath+"/instance/profileExists",schemaPath:"#/$defs/InstanceInfo/properties/profileExists/type",keyword:"type",params:{type: "boolean"},message:"must be boolean"}];
return false;
}
var valid10 = _errs49 === errors;
}
else {
var valid10 = true;
}
if(valid10){
if(data15.protocolLocked !== undefined){
const _errs51 = errors;
if(typeof data15.protocolLocked !== "boolean"){
validate103.errors = [{instancePath:instancePath+"/instance/protocolLocked",schemaPath:"#/$defs/InstanceInfo/properties/protocolLocked/type",keyword:"type",params:{type: "boolean"},message:"must be boolean"}];
return false;
}
var valid10 = _errs51 === errors;
}
else {
var valid10 = true;
}
if(valid10){
if(data15.safetyNumber !== undefined){
const _errs53 = errors;
if(typeof data15.safetyNumber !== "string"){
validate103.errors = [{instancePath:instancePath+"/instance/safetyNumber",schemaPath:"#/$defs/InstanceInfo/properties/safetyNumber/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid10 = _errs53 === errors;
}
else {
var valid10 = true;
}
}
}
}
}
}
}
}
}
}
}
else {
validate103.errors = [{instancePath:instancePath+"/instance",schemaPath:"#/$defs/InstanceInfo/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
var valid0 = _errs32 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.operations !== undefined){
let data26 = data.operations;
const _errs55 = errors;
if((!(Array.isArray(data26))) && (data26 !== null)){
validate103.errors = [{instancePath:instancePath+"/operations",schemaPath:"#/properties/operations/type",keyword:"type",params:{type: schema111.properties.operations.type},message:"must be array,null"}];
return false;
}
if(errors === _errs55){
if(Array.isArray(data26)){
var valid12 = true;
const len5 = data26.length;
for(let i5=0; i5<len5; i5++){
const _errs57 = errors;
if(!(validate106(data26[i5], {instancePath:instancePath+"/operations/" + i5,parentData:data26,parentDataProperty:i5,rootData,dynamicAnchors}))){
vErrors = vErrors === null ? validate106.errors : vErrors.concat(validate106.errors);
errors = vErrors.length;
}
var valid12 = _errs57 === errors;
if(!valid12){
break;
}
}
}
}
var valid0 = _errs55 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.presenceEnabled !== undefined){
let data28 = data.presenceEnabled;
const _errs58 = errors;
if((typeof data28 !== "boolean") && (data28 !== null)){
validate103.errors = [{instancePath:instancePath+"/presenceEnabled",schemaPath:"#/properties/presenceEnabled/type",keyword:"type",params:{type: schema111.properties.presenceEnabled.type},message:"must be boolean,null"}];
return false;
}
var valid0 = _errs58 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.providerErrors !== undefined){
let data29 = data.providerErrors;
const _errs60 = errors;
if(errors === _errs60){
if(Array.isArray(data29)){
var valid13 = true;
const len6 = data29.length;
for(let i6=0; i6<len6; i6++){
let data30 = data29[i6];
const _errs62 = errors;
const _errs63 = errors;
if(errors === _errs63){
if(data30 && typeof data30 == "object" && !Array.isArray(data30)){
let missing4;
if(((((data30.id === undefined) && (missing4 = "id")) || ((data30.code === undefined) && (missing4 = "code"))) || ((data30.message === undefined) && (missing4 = "message"))) || ((data30.retryable === undefined) && (missing4 = "retryable"))){
validate103.errors = [{instancePath:instancePath+"/providerErrors/" + i6,schemaPath:"#/$defs/ProviderStatus/required",keyword:"required",params:{missingProperty: missing4},message:"must have required property '"+missing4+"'"}];
return false;
}
else {
if(data30.code !== undefined){
const _errs65 = errors;
if(typeof data30.code !== "string"){
validate103.errors = [{instancePath:instancePath+"/providerErrors/" + i6+"/code",schemaPath:"#/$defs/ProviderStatus/properties/code/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid15 = _errs65 === errors;
}
else {
var valid15 = true;
}
if(valid15){
if(data30.id !== undefined){
const _errs67 = errors;
if(typeof data30.id !== "string"){
validate103.errors = [{instancePath:instancePath+"/providerErrors/" + i6+"/id",schemaPath:"#/$defs/ProviderStatus/properties/id/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid15 = _errs67 === errors;
}
else {
var valid15 = true;
}
if(valid15){
if(data30.message !== undefined){
const _errs69 = errors;
if(typeof data30.message !== "string"){
validate103.errors = [{instancePath:instancePath+"/providerErrors/" + i6+"/message",schemaPath:"#/$defs/ProviderStatus/properties/message/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid15 = _errs69 === errors;
}
else {
var valid15 = true;
}
if(valid15){
if(data30.retryable !== undefined){
const _errs71 = errors;
if(typeof data30.retryable !== "boolean"){
validate103.errors = [{instancePath:instancePath+"/providerErrors/" + i6+"/retryable",schemaPath:"#/$defs/ProviderStatus/properties/retryable/type",keyword:"type",params:{type: "boolean"},message:"must be boolean"}];
return false;
}
var valid15 = _errs71 === errors;
}
else {
var valid15 = true;
}
}
}
}
}
}
else {
validate103.errors = [{instancePath:instancePath+"/providerErrors/" + i6,schemaPath:"#/$defs/ProviderStatus/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
var valid13 = _errs62 === errors;
if(!valid13){
break;
}
}
}
else {
validate103.errors = [{instancePath:instancePath+"/providerErrors",schemaPath:"#/properties/providerErrors/type",keyword:"type",params:{type: "array"},message:"must be array"}];
return false;
}
}
var valid0 = _errs60 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.revision !== undefined){
const _errs73 = errors;
if(typeof data.revision !== "string"){
validate103.errors = [{instancePath:instancePath+"/revision",schemaPath:"#/properties/revision/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs73 === errors;
}
else {
var valid0 = true;
}
}
}
}
}
}
}
}
}
}
}
else {
validate103.errors = [{instancePath,schemaPath:"#/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
validate103.errors = vErrors;
return errors === 0;
}
validate103.evaluated = {"props":{"activity":true,"commandHistory":true,"conversations":true,"inputHistory":true,"instance":true,"operations":true,"presenceEnabled":true,"providerErrors":true,"revision":true},"dynamicProps":false,"dynamicItems":false};

export const unlock_error = validate110;
const schema124 = {"$schema":"https://json-schema.org/draft/2020-12/schema","additionalProperties":false,"properties":{"code":{"type":"string"},"message":{"type":"string"}},"required":["code","message"],"title":"ChatError","type":"object"};

function validate110(data, {instancePath="", parentData, parentDataProperty, rootData=data, dynamicAnchors={}}={}){
let vErrors = null;
let errors = 0;
const evaluated0 = validate110.evaluated;
if(evaluated0.dynamicProps){
evaluated0.props = undefined;
}
if(evaluated0.dynamicItems){
evaluated0.items = undefined;
}
if(errors === 0){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing0;
if(((data.code === undefined) && (missing0 = "code")) || ((data.message === undefined) && (missing0 = "message"))){
validate110.errors = [{instancePath,schemaPath:"#/required",keyword:"required",params:{missingProperty: missing0},message:"must have required property '"+missing0+"'"}];
return false;
}
else {
const _errs1 = errors;
for(const key0 in data){
if(!((key0 === "code") || (key0 === "message"))){
validate110.errors = [{instancePath,schemaPath:"#/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key0},message:"must NOT have additional properties"}];
return false;
break;
}
}
if(_errs1 === errors){
if(data.code !== undefined){
const _errs2 = errors;
if(typeof data.code !== "string"){
validate110.errors = [{instancePath:instancePath+"/code",schemaPath:"#/properties/code/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs2 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.message !== undefined){
const _errs4 = errors;
if(typeof data.message !== "string"){
validate110.errors = [{instancePath:instancePath+"/message",schemaPath:"#/properties/message/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs4 === errors;
}
else {
var valid0 = true;
}
}
}
}
}
else {
validate110.errors = [{instancePath,schemaPath:"#/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
validate110.errors = vErrors;
return errors === 0;
}
validate110.evaluated = {"props":true,"dynamicProps":false,"dynamicItems":false};

export const lock_args = validate111;
const schema125 = {"$schema":"https://json-schema.org/draft/2020-12/schema","additionalProperties":false,"title":"ChatLockArgs","type":"object"};

function validate111(data, {instancePath="", parentData, parentDataProperty, rootData=data, dynamicAnchors={}}={}){
let vErrors = null;
let errors = 0;
const evaluated0 = validate111.evaluated;
if(evaluated0.dynamicProps){
evaluated0.props = undefined;
}
if(evaluated0.dynamicItems){
evaluated0.items = undefined;
}
if(errors === 0){
if(data && typeof data == "object" && !Array.isArray(data)){
for(const key0 in data){
validate111.errors = [{instancePath,schemaPath:"#/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key0},message:"must NOT have additional properties"}];
return false;
break;
}
}
else {
validate111.errors = [{instancePath,schemaPath:"#/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
validate111.errors = vErrors;
return errors === 0;
}
validate111.evaluated = {"props":true,"dynamicProps":false,"dynamicItems":false};

export const lock_output = validate112;
const schema126 = {"$schema":"https://json-schema.org/draft/2020-12/schema","properties":{"archiveExists":{"type":"boolean"},"bootId":{"type":"string"},"capabilities":{"items":{"type":"string"},"type":"array"},"id":{"type":"string"},"label":{"type":"string"},"locked":{"type":"boolean"},"profileExists":{"type":"boolean"},"protocolLocked":{"type":"boolean"},"safetyNumber":{"type":"string"}},"required":["id","label","bootId","locked","protocolLocked","profileExists","archiveExists","safetyNumber","capabilities"],"title":"InstanceInfo","type":"object"};

function validate112(data, {instancePath="", parentData, parentDataProperty, rootData=data, dynamicAnchors={}}={}){
let vErrors = null;
let errors = 0;
const evaluated0 = validate112.evaluated;
if(evaluated0.dynamicProps){
evaluated0.props = undefined;
}
if(evaluated0.dynamicItems){
evaluated0.items = undefined;
}
if(errors === 0){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing0;
if((((((((((data.id === undefined) && (missing0 = "id")) || ((data.label === undefined) && (missing0 = "label"))) || ((data.bootId === undefined) && (missing0 = "bootId"))) || ((data.locked === undefined) && (missing0 = "locked"))) || ((data.protocolLocked === undefined) && (missing0 = "protocolLocked"))) || ((data.profileExists === undefined) && (missing0 = "profileExists"))) || ((data.archiveExists === undefined) && (missing0 = "archiveExists"))) || ((data.safetyNumber === undefined) && (missing0 = "safetyNumber"))) || ((data.capabilities === undefined) && (missing0 = "capabilities"))){
validate112.errors = [{instancePath,schemaPath:"#/required",keyword:"required",params:{missingProperty: missing0},message:"must have required property '"+missing0+"'"}];
return false;
}
else {
if(data.archiveExists !== undefined){
const _errs1 = errors;
if(typeof data.archiveExists !== "boolean"){
validate112.errors = [{instancePath:instancePath+"/archiveExists",schemaPath:"#/properties/archiveExists/type",keyword:"type",params:{type: "boolean"},message:"must be boolean"}];
return false;
}
var valid0 = _errs1 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.bootId !== undefined){
const _errs3 = errors;
if(typeof data.bootId !== "string"){
validate112.errors = [{instancePath:instancePath+"/bootId",schemaPath:"#/properties/bootId/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs3 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.capabilities !== undefined){
let data2 = data.capabilities;
const _errs5 = errors;
if(errors === _errs5){
if(Array.isArray(data2)){
var valid1 = true;
const len0 = data2.length;
for(let i0=0; i0<len0; i0++){
const _errs7 = errors;
if(typeof data2[i0] !== "string"){
validate112.errors = [{instancePath:instancePath+"/capabilities/" + i0,schemaPath:"#/properties/capabilities/items/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid1 = _errs7 === errors;
if(!valid1){
break;
}
}
}
else {
validate112.errors = [{instancePath:instancePath+"/capabilities",schemaPath:"#/properties/capabilities/type",keyword:"type",params:{type: "array"},message:"must be array"}];
return false;
}
}
var valid0 = _errs5 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.id !== undefined){
const _errs9 = errors;
if(typeof data.id !== "string"){
validate112.errors = [{instancePath:instancePath+"/id",schemaPath:"#/properties/id/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs9 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.label !== undefined){
const _errs11 = errors;
if(typeof data.label !== "string"){
validate112.errors = [{instancePath:instancePath+"/label",schemaPath:"#/properties/label/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs11 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.locked !== undefined){
const _errs13 = errors;
if(typeof data.locked !== "boolean"){
validate112.errors = [{instancePath:instancePath+"/locked",schemaPath:"#/properties/locked/type",keyword:"type",params:{type: "boolean"},message:"must be boolean"}];
return false;
}
var valid0 = _errs13 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.profileExists !== undefined){
const _errs15 = errors;
if(typeof data.profileExists !== "boolean"){
validate112.errors = [{instancePath:instancePath+"/profileExists",schemaPath:"#/properties/profileExists/type",keyword:"type",params:{type: "boolean"},message:"must be boolean"}];
return false;
}
var valid0 = _errs15 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.protocolLocked !== undefined){
const _errs17 = errors;
if(typeof data.protocolLocked !== "boolean"){
validate112.errors = [{instancePath:instancePath+"/protocolLocked",schemaPath:"#/properties/protocolLocked/type",keyword:"type",params:{type: "boolean"},message:"must be boolean"}];
return false;
}
var valid0 = _errs17 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.safetyNumber !== undefined){
const _errs19 = errors;
if(typeof data.safetyNumber !== "string"){
validate112.errors = [{instancePath:instancePath+"/safetyNumber",schemaPath:"#/properties/safetyNumber/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs19 === errors;
}
else {
var valid0 = true;
}
}
}
}
}
}
}
}
}
}
}
else {
validate112.errors = [{instancePath,schemaPath:"#/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
validate112.errors = vErrors;
return errors === 0;
}
validate112.evaluated = {"props":{"archiveExists":true,"bootId":true,"capabilities":true,"id":true,"label":true,"locked":true,"profileExists":true,"protocolLocked":true,"safetyNumber":true},"dynamicProps":false,"dynamicItems":false};

export const lock_error = validate113;
const schema127 = {"$schema":"https://json-schema.org/draft/2020-12/schema","additionalProperties":false,"properties":{"code":{"type":"string"},"message":{"type":"string"}},"required":["code","message"],"title":"ChatError","type":"object"};

function validate113(data, {instancePath="", parentData, parentDataProperty, rootData=data, dynamicAnchors={}}={}){
let vErrors = null;
let errors = 0;
const evaluated0 = validate113.evaluated;
if(evaluated0.dynamicProps){
evaluated0.props = undefined;
}
if(evaluated0.dynamicItems){
evaluated0.items = undefined;
}
if(errors === 0){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing0;
if(((data.code === undefined) && (missing0 = "code")) || ((data.message === undefined) && (missing0 = "message"))){
validate113.errors = [{instancePath,schemaPath:"#/required",keyword:"required",params:{missingProperty: missing0},message:"must have required property '"+missing0+"'"}];
return false;
}
else {
const _errs1 = errors;
for(const key0 in data){
if(!((key0 === "code") || (key0 === "message"))){
validate113.errors = [{instancePath,schemaPath:"#/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key0},message:"must NOT have additional properties"}];
return false;
break;
}
}
if(_errs1 === errors){
if(data.code !== undefined){
const _errs2 = errors;
if(typeof data.code !== "string"){
validate113.errors = [{instancePath:instancePath+"/code",schemaPath:"#/properties/code/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs2 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.message !== undefined){
const _errs4 = errors;
if(typeof data.message !== "string"){
validate113.errors = [{instancePath:instancePath+"/message",schemaPath:"#/properties/message/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs4 === errors;
}
else {
var valid0 = true;
}
}
}
}
}
else {
validate113.errors = [{instancePath,schemaPath:"#/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
validate113.errors = vErrors;
return errors === 0;
}
validate113.evaluated = {"props":true,"dynamicProps":false,"dynamicItems":false};

export const disconnect_args = validate114;
const schema128 = {"$schema":"https://json-schema.org/draft/2020-12/schema","additionalProperties":false,"title":"ChatDisconnectArgs","type":"object"};

function validate114(data, {instancePath="", parentData, parentDataProperty, rootData=data, dynamicAnchors={}}={}){
let vErrors = null;
let errors = 0;
const evaluated0 = validate114.evaluated;
if(evaluated0.dynamicProps){
evaluated0.props = undefined;
}
if(evaluated0.dynamicItems){
evaluated0.items = undefined;
}
if(errors === 0){
if(data && typeof data == "object" && !Array.isArray(data)){
for(const key0 in data){
validate114.errors = [{instancePath,schemaPath:"#/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key0},message:"must NOT have additional properties"}];
return false;
break;
}
}
else {
validate114.errors = [{instancePath,schemaPath:"#/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
validate114.errors = vErrors;
return errors === 0;
}
validate114.evaluated = {"props":true,"dynamicProps":false,"dynamicItems":false};

export const disconnect_output = validate115;
const schema129 = {"$defs":{"Activity":{"description":"Authenticated state changes observed by this profile, retained before publication.","properties":{"conversation":{"type":"string"},"id":{"type":"string"},"kind":{"type":"string"},"text":{"type":"string"},"timestamp":{"format":"uint64","minimum":0,"type":"integer"}},"required":["id","conversation","kind","text","timestamp"],"type":"object"},"CommandOutput":{"oneOf":[{"properties":{"commands":{"items":{"$ref":"#/$defs/CommandSpec"},"type":"array"},"kind":{"const":"help","type":"string"}},"required":["kind","commands"],"type":"object"},{"properties":{"channels":{"items":{"$ref":"#/$defs/DirectoryEntry"},"type":"array"},"kind":{"const":"directory","type":"string"}},"required":["kind","channels"],"type":"object"},{"properties":{"channel":{"type":"string"},"expires":{"format":"uint64","minimum":0,"type":"integer"},"kind":{"const":"invitation","type":"string"},"link":{"type":"string"},"localOnly":{"default":false,"type":"boolean"}},"required":["kind","channel","link","expires"],"type":"object"},{"properties":{"kind":{"const":"text","type":"string"},"text":{"type":"string"},"title":{"type":"string"}},"required":["kind","title","text"],"type":"object"},{"properties":{"kind":{"const":"status","type":"string"},"text":{"type":"string"}},"required":["kind","text"],"type":"object"},{"properties":{"conversation":{"type":"string"},"kind":{"const":"close","type":"string"}},"required":["kind","conversation"],"type":"object"}]},"CommandSpec":{"properties":{"available":{"type":"boolean"},"capability":{"type":["string","null"]},"description":{"type":"string"},"name":{"type":"string"},"scope":{"type":"string"},"usage":{"type":"string"}},"required":["name","usage","description","scope","available"],"type":"object"},"Conversation":{"properties":{"active":{"type":"boolean"},"channelId":{"type":"string"},"commands":{"default":[],"items":{"$ref":"#/$defs/CommandSpec"},"type":"array"},"directory":{"default":null,"type":["string","null"]},"id":{"type":"string"},"inputLimitBytes":{"default":12000,"format":"uint","minimum":0,"type":"integer"},"kind":{"$ref":"#/$defs/ConversationKind"},"lastMessageId":{"type":["string","null"]},"members":{"items":{"$ref":"#/$defs/Member"},"type":"array"},"name":{"type":"string"},"owner":{"type":"boolean"},"provider":{"default":null,"type":["string","null"]},"topic":{"type":"string"},"unread":{"format":"uint32","minimum":0,"type":"integer"},"visibility":{"default":null,"type":["string","null"]}},"required":["id","channelId","kind","name","topic","active","owner","members","unread"],"type":"object"},"ConversationKind":{"enum":["channel","query","archive"],"type":"string"},"DirectoryEntry":{"properties":{"conversation":{"type":["string","null"]},"joined":{"type":"boolean"},"name":{"type":"string"}},"required":["name","joined"],"type":"object"},"InputHistoryEntry":{"properties":{"conversation":{"type":["string","null"]},"text":{"type":"string"}},"required":["text"],"type":"object"},"InstanceInfo":{"properties":{"archiveExists":{"type":"boolean"},"bootId":{"type":"string"},"capabilities":{"items":{"type":"string"},"type":"array"},"id":{"type":"string"},"label":{"type":"string"},"locked":{"type":"boolean"},"profileExists":{"type":"boolean"},"protocolLocked":{"type":"boolean"},"safetyNumber":{"type":"string"}},"required":["id","label","bootId","locked","protocolLocked","profileExists","archiveExists","safetyNumber","capabilities"],"type":"object"},"Member":{"properties":{"capabilities":{"default":[],"items":{"type":"string"},"type":"array"},"id":{"type":"string"},"isSelf":{"type":"boolean"},"nickname":{"type":"string"},"recentlyActive":{"default":null,"type":["boolean","null"]}},"required":["id","nickname","isSelf"],"type":"object"},"OperationDetail":{"description":"Safe metadata plus the protected result retained in the encrypted operation journal.","properties":{"action":{"type":"string"},"conversation":{"type":["string","null"]},"id":{"type":"string"},"instance":{"type":"string"},"message":{"type":["string","null"]},"network":{"default":null,"type":["string","null"]},"output":{"anyOf":[{"$ref":"#/$defs/CommandOutput"},{"type":"null"}]},"started":{"format":"uint64","minimum":0,"type":"integer"},"state":{"type":"string"}},"required":["id","instance","action","started","state"],"type":"object"},"ProviderStatus":{"properties":{"code":{"type":"string"},"id":{"type":"string"},"message":{"type":"string"},"retryable":{"type":"boolean"}},"required":["id","code","message","retryable"],"type":"object"}},"$schema":"https://json-schema.org/draft/2020-12/schema","properties":{"activity":{"default":null,"items":{"$ref":"#/$defs/Activity"},"type":["array","null"]},"commandHistory":{"items":{"type":"string"},"type":"array"},"conversations":{"items":{"$ref":"#/$defs/Conversation"},"type":"array"},"inputHistory":{"items":{"$ref":"#/$defs/InputHistoryEntry"},"type":"array"},"instance":{"$ref":"#/$defs/InstanceInfo"},"operations":{"default":null,"items":{"$ref":"#/$defs/OperationDetail"},"type":["array","null"]},"presenceEnabled":{"default":null,"type":["boolean","null"]},"providerErrors":{"default":[],"items":{"$ref":"#/$defs/ProviderStatus"},"type":"array"},"revision":{"type":"string"}},"required":["instance","revision","conversations","commandHistory","inputHistory"],"title":"Snapshot","type":"object"};
const schema130 = {"description":"Authenticated state changes observed by this profile, retained before publication.","properties":{"conversation":{"type":"string"},"id":{"type":"string"},"kind":{"type":"string"},"text":{"type":"string"},"timestamp":{"format":"uint64","minimum":0,"type":"integer"}},"required":["id","conversation","kind","text","timestamp"],"type":"object"};
const schema135 = {"properties":{"conversation":{"type":["string","null"]},"text":{"type":"string"}},"required":["text"],"type":"object"};
const schema136 = {"properties":{"archiveExists":{"type":"boolean"},"bootId":{"type":"string"},"capabilities":{"items":{"type":"string"},"type":"array"},"id":{"type":"string"},"label":{"type":"string"},"locked":{"type":"boolean"},"profileExists":{"type":"boolean"},"protocolLocked":{"type":"boolean"},"safetyNumber":{"type":"string"}},"required":["id","label","bootId","locked","protocolLocked","profileExists","archiveExists","safetyNumber","capabilities"],"type":"object"};
const schema141 = {"properties":{"code":{"type":"string"},"id":{"type":"string"},"message":{"type":"string"},"retryable":{"type":"boolean"}},"required":["id","code","message","retryable"],"type":"object"};
const schema131 = {"properties":{"active":{"type":"boolean"},"channelId":{"type":"string"},"commands":{"default":[],"items":{"$ref":"#/$defs/CommandSpec"},"type":"array"},"directory":{"default":null,"type":["string","null"]},"id":{"type":"string"},"inputLimitBytes":{"default":12000,"format":"uint","minimum":0,"type":"integer"},"kind":{"$ref":"#/$defs/ConversationKind"},"lastMessageId":{"type":["string","null"]},"members":{"items":{"$ref":"#/$defs/Member"},"type":"array"},"name":{"type":"string"},"owner":{"type":"boolean"},"provider":{"default":null,"type":["string","null"]},"topic":{"type":"string"},"unread":{"format":"uint32","minimum":0,"type":"integer"},"visibility":{"default":null,"type":["string","null"]}},"required":["id","channelId","kind","name","topic","active","owner","members","unread"],"type":"object"};
const schema132 = {"properties":{"available":{"type":"boolean"},"capability":{"type":["string","null"]},"description":{"type":"string"},"name":{"type":"string"},"scope":{"type":"string"},"usage":{"type":"string"}},"required":["name","usage","description","scope","available"],"type":"object"};
const schema133 = {"enum":["channel","query","archive"],"type":"string"};
const schema134 = {"properties":{"capabilities":{"default":[],"items":{"type":"string"},"type":"array"},"id":{"type":"string"},"isSelf":{"type":"boolean"},"nickname":{"type":"string"},"recentlyActive":{"default":null,"type":["boolean","null"]}},"required":["id","nickname","isSelf"],"type":"object"};

function validate116(data, {instancePath="", parentData, parentDataProperty, rootData=data, dynamicAnchors={}}={}){
let vErrors = null;
let errors = 0;
const evaluated0 = validate116.evaluated;
if(evaluated0.dynamicProps){
evaluated0.props = undefined;
}
if(evaluated0.dynamicItems){
evaluated0.items = undefined;
}
if(errors === 0){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing0;
if((((((((((data.id === undefined) && (missing0 = "id")) || ((data.channelId === undefined) && (missing0 = "channelId"))) || ((data.kind === undefined) && (missing0 = "kind"))) || ((data.name === undefined) && (missing0 = "name"))) || ((data.topic === undefined) && (missing0 = "topic"))) || ((data.active === undefined) && (missing0 = "active"))) || ((data.owner === undefined) && (missing0 = "owner"))) || ((data.members === undefined) && (missing0 = "members"))) || ((data.unread === undefined) && (missing0 = "unread"))){
validate116.errors = [{instancePath,schemaPath:"#/required",keyword:"required",params:{missingProperty: missing0},message:"must have required property '"+missing0+"'"}];
return false;
}
else {
if(data.active !== undefined){
const _errs1 = errors;
if(typeof data.active !== "boolean"){
validate116.errors = [{instancePath:instancePath+"/active",schemaPath:"#/properties/active/type",keyword:"type",params:{type: "boolean"},message:"must be boolean"}];
return false;
}
var valid0 = _errs1 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.channelId !== undefined){
const _errs3 = errors;
if(typeof data.channelId !== "string"){
validate116.errors = [{instancePath:instancePath+"/channelId",schemaPath:"#/properties/channelId/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs3 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.commands !== undefined){
let data2 = data.commands;
const _errs5 = errors;
if(errors === _errs5){
if(Array.isArray(data2)){
var valid1 = true;
const len0 = data2.length;
for(let i0=0; i0<len0; i0++){
let data3 = data2[i0];
const _errs7 = errors;
const _errs8 = errors;
if(errors === _errs8){
if(data3 && typeof data3 == "object" && !Array.isArray(data3)){
let missing1;
if((((((data3.name === undefined) && (missing1 = "name")) || ((data3.usage === undefined) && (missing1 = "usage"))) || ((data3.description === undefined) && (missing1 = "description"))) || ((data3.scope === undefined) && (missing1 = "scope"))) || ((data3.available === undefined) && (missing1 = "available"))){
validate116.errors = [{instancePath:instancePath+"/commands/" + i0,schemaPath:"#/$defs/CommandSpec/required",keyword:"required",params:{missingProperty: missing1},message:"must have required property '"+missing1+"'"}];
return false;
}
else {
if(data3.available !== undefined){
const _errs10 = errors;
if(typeof data3.available !== "boolean"){
validate116.errors = [{instancePath:instancePath+"/commands/" + i0+"/available",schemaPath:"#/$defs/CommandSpec/properties/available/type",keyword:"type",params:{type: "boolean"},message:"must be boolean"}];
return false;
}
var valid3 = _errs10 === errors;
}
else {
var valid3 = true;
}
if(valid3){
if(data3.capability !== undefined){
let data5 = data3.capability;
const _errs12 = errors;
if((typeof data5 !== "string") && (data5 !== null)){
validate116.errors = [{instancePath:instancePath+"/commands/" + i0+"/capability",schemaPath:"#/$defs/CommandSpec/properties/capability/type",keyword:"type",params:{type: schema132.properties.capability.type},message:"must be string,null"}];
return false;
}
var valid3 = _errs12 === errors;
}
else {
var valid3 = true;
}
if(valid3){
if(data3.description !== undefined){
const _errs14 = errors;
if(typeof data3.description !== "string"){
validate116.errors = [{instancePath:instancePath+"/commands/" + i0+"/description",schemaPath:"#/$defs/CommandSpec/properties/description/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid3 = _errs14 === errors;
}
else {
var valid3 = true;
}
if(valid3){
if(data3.name !== undefined){
const _errs16 = errors;
if(typeof data3.name !== "string"){
validate116.errors = [{instancePath:instancePath+"/commands/" + i0+"/name",schemaPath:"#/$defs/CommandSpec/properties/name/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid3 = _errs16 === errors;
}
else {
var valid3 = true;
}
if(valid3){
if(data3.scope !== undefined){
const _errs18 = errors;
if(typeof data3.scope !== "string"){
validate116.errors = [{instancePath:instancePath+"/commands/" + i0+"/scope",schemaPath:"#/$defs/CommandSpec/properties/scope/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid3 = _errs18 === errors;
}
else {
var valid3 = true;
}
if(valid3){
if(data3.usage !== undefined){
const _errs20 = errors;
if(typeof data3.usage !== "string"){
validate116.errors = [{instancePath:instancePath+"/commands/" + i0+"/usage",schemaPath:"#/$defs/CommandSpec/properties/usage/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid3 = _errs20 === errors;
}
else {
var valid3 = true;
}
}
}
}
}
}
}
}
else {
validate116.errors = [{instancePath:instancePath+"/commands/" + i0,schemaPath:"#/$defs/CommandSpec/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
var valid1 = _errs7 === errors;
if(!valid1){
break;
}
}
}
else {
validate116.errors = [{instancePath:instancePath+"/commands",schemaPath:"#/properties/commands/type",keyword:"type",params:{type: "array"},message:"must be array"}];
return false;
}
}
var valid0 = _errs5 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.directory !== undefined){
let data10 = data.directory;
const _errs22 = errors;
if((typeof data10 !== "string") && (data10 !== null)){
validate116.errors = [{instancePath:instancePath+"/directory",schemaPath:"#/properties/directory/type",keyword:"type",params:{type: schema131.properties.directory.type},message:"must be string,null"}];
return false;
}
var valid0 = _errs22 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.id !== undefined){
const _errs24 = errors;
if(typeof data.id !== "string"){
validate116.errors = [{instancePath:instancePath+"/id",schemaPath:"#/properties/id/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs24 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.inputLimitBytes !== undefined){
let data12 = data.inputLimitBytes;
const _errs26 = errors;
if(!(((typeof data12 == "number") && (!(data12 % 1) && !isNaN(data12))) && (isFinite(data12)))){
validate116.errors = [{instancePath:instancePath+"/inputLimitBytes",schemaPath:"#/properties/inputLimitBytes/type",keyword:"type",params:{type: "integer"},message:"must be integer"}];
return false;
}
if(errors === _errs26){
if((typeof data12 == "number") && (isFinite(data12))){
if(data12 < 0 || isNaN(data12)){
validate116.errors = [{instancePath:instancePath+"/inputLimitBytes",schemaPath:"#/properties/inputLimitBytes/minimum",keyword:"minimum",params:{comparison: ">=", limit: 0},message:"must be >= 0"}];
return false;
}
}
}
var valid0 = _errs26 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.kind !== undefined){
let data13 = data.kind;
const _errs28 = errors;
if(typeof data13 !== "string"){
validate116.errors = [{instancePath:instancePath+"/kind",schemaPath:"#/$defs/ConversationKind/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
if(!(((data13 === "channel") || (data13 === "query")) || (data13 === "archive"))){
validate116.errors = [{instancePath:instancePath+"/kind",schemaPath:"#/$defs/ConversationKind/enum",keyword:"enum",params:{allowedValues: schema133.enum},message:"must be equal to one of the allowed values"}];
return false;
}
var valid0 = _errs28 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.lastMessageId !== undefined){
let data14 = data.lastMessageId;
const _errs31 = errors;
if((typeof data14 !== "string") && (data14 !== null)){
validate116.errors = [{instancePath:instancePath+"/lastMessageId",schemaPath:"#/properties/lastMessageId/type",keyword:"type",params:{type: schema131.properties.lastMessageId.type},message:"must be string,null"}];
return false;
}
var valid0 = _errs31 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.members !== undefined){
let data15 = data.members;
const _errs33 = errors;
if(errors === _errs33){
if(Array.isArray(data15)){
var valid5 = true;
const len1 = data15.length;
for(let i1=0; i1<len1; i1++){
let data16 = data15[i1];
const _errs35 = errors;
const _errs36 = errors;
if(errors === _errs36){
if(data16 && typeof data16 == "object" && !Array.isArray(data16)){
let missing2;
if((((data16.id === undefined) && (missing2 = "id")) || ((data16.nickname === undefined) && (missing2 = "nickname"))) || ((data16.isSelf === undefined) && (missing2 = "isSelf"))){
validate116.errors = [{instancePath:instancePath+"/members/" + i1,schemaPath:"#/$defs/Member/required",keyword:"required",params:{missingProperty: missing2},message:"must have required property '"+missing2+"'"}];
return false;
}
else {
if(data16.capabilities !== undefined){
let data17 = data16.capabilities;
const _errs38 = errors;
if(errors === _errs38){
if(Array.isArray(data17)){
var valid8 = true;
const len2 = data17.length;
for(let i2=0; i2<len2; i2++){
const _errs40 = errors;
if(typeof data17[i2] !== "string"){
validate116.errors = [{instancePath:instancePath+"/members/" + i1+"/capabilities/" + i2,schemaPath:"#/$defs/Member/properties/capabilities/items/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid8 = _errs40 === errors;
if(!valid8){
break;
}
}
}
else {
validate116.errors = [{instancePath:instancePath+"/members/" + i1+"/capabilities",schemaPath:"#/$defs/Member/properties/capabilities/type",keyword:"type",params:{type: "array"},message:"must be array"}];
return false;
}
}
var valid7 = _errs38 === errors;
}
else {
var valid7 = true;
}
if(valid7){
if(data16.id !== undefined){
const _errs42 = errors;
if(typeof data16.id !== "string"){
validate116.errors = [{instancePath:instancePath+"/members/" + i1+"/id",schemaPath:"#/$defs/Member/properties/id/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid7 = _errs42 === errors;
}
else {
var valid7 = true;
}
if(valid7){
if(data16.isSelf !== undefined){
const _errs44 = errors;
if(typeof data16.isSelf !== "boolean"){
validate116.errors = [{instancePath:instancePath+"/members/" + i1+"/isSelf",schemaPath:"#/$defs/Member/properties/isSelf/type",keyword:"type",params:{type: "boolean"},message:"must be boolean"}];
return false;
}
var valid7 = _errs44 === errors;
}
else {
var valid7 = true;
}
if(valid7){
if(data16.nickname !== undefined){
const _errs46 = errors;
if(typeof data16.nickname !== "string"){
validate116.errors = [{instancePath:instancePath+"/members/" + i1+"/nickname",schemaPath:"#/$defs/Member/properties/nickname/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid7 = _errs46 === errors;
}
else {
var valid7 = true;
}
if(valid7){
if(data16.recentlyActive !== undefined){
let data22 = data16.recentlyActive;
const _errs48 = errors;
if((typeof data22 !== "boolean") && (data22 !== null)){
validate116.errors = [{instancePath:instancePath+"/members/" + i1+"/recentlyActive",schemaPath:"#/$defs/Member/properties/recentlyActive/type",keyword:"type",params:{type: schema134.properties.recentlyActive.type},message:"must be boolean,null"}];
return false;
}
var valid7 = _errs48 === errors;
}
else {
var valid7 = true;
}
}
}
}
}
}
}
else {
validate116.errors = [{instancePath:instancePath+"/members/" + i1,schemaPath:"#/$defs/Member/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
var valid5 = _errs35 === errors;
if(!valid5){
break;
}
}
}
else {
validate116.errors = [{instancePath:instancePath+"/members",schemaPath:"#/properties/members/type",keyword:"type",params:{type: "array"},message:"must be array"}];
return false;
}
}
var valid0 = _errs33 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.name !== undefined){
const _errs50 = errors;
if(typeof data.name !== "string"){
validate116.errors = [{instancePath:instancePath+"/name",schemaPath:"#/properties/name/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs50 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.owner !== undefined){
const _errs52 = errors;
if(typeof data.owner !== "boolean"){
validate116.errors = [{instancePath:instancePath+"/owner",schemaPath:"#/properties/owner/type",keyword:"type",params:{type: "boolean"},message:"must be boolean"}];
return false;
}
var valid0 = _errs52 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.provider !== undefined){
let data25 = data.provider;
const _errs54 = errors;
if((typeof data25 !== "string") && (data25 !== null)){
validate116.errors = [{instancePath:instancePath+"/provider",schemaPath:"#/properties/provider/type",keyword:"type",params:{type: schema131.properties.provider.type},message:"must be string,null"}];
return false;
}
var valid0 = _errs54 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.topic !== undefined){
const _errs56 = errors;
if(typeof data.topic !== "string"){
validate116.errors = [{instancePath:instancePath+"/topic",schemaPath:"#/properties/topic/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs56 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.unread !== undefined){
let data27 = data.unread;
const _errs58 = errors;
if(!(((typeof data27 == "number") && (!(data27 % 1) && !isNaN(data27))) && (isFinite(data27)))){
validate116.errors = [{instancePath:instancePath+"/unread",schemaPath:"#/properties/unread/type",keyword:"type",params:{type: "integer"},message:"must be integer"}];
return false;
}
if(errors === _errs58){
if((typeof data27 == "number") && (isFinite(data27))){
if(data27 < 0 || isNaN(data27)){
validate116.errors = [{instancePath:instancePath+"/unread",schemaPath:"#/properties/unread/minimum",keyword:"minimum",params:{comparison: ">=", limit: 0},message:"must be >= 0"}];
return false;
}
}
}
var valid0 = _errs58 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.visibility !== undefined){
let data28 = data.visibility;
const _errs60 = errors;
if((typeof data28 !== "string") && (data28 !== null)){
validate116.errors = [{instancePath:instancePath+"/visibility",schemaPath:"#/properties/visibility/type",keyword:"type",params:{type: schema131.properties.visibility.type},message:"must be string,null"}];
return false;
}
var valid0 = _errs60 === errors;
}
else {
var valid0 = true;
}
}
}
}
}
}
}
}
}
}
}
}
}
}
}
}
}
else {
validate116.errors = [{instancePath,schemaPath:"#/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
validate116.errors = vErrors;
return errors === 0;
}
validate116.evaluated = {"props":{"active":true,"channelId":true,"commands":true,"directory":true,"id":true,"inputLimitBytes":true,"kind":true,"lastMessageId":true,"members":true,"name":true,"owner":true,"provider":true,"topic":true,"unread":true,"visibility":true},"dynamicProps":false,"dynamicItems":false};

const schema137 = {"description":"Safe metadata plus the protected result retained in the encrypted operation journal.","properties":{"action":{"type":"string"},"conversation":{"type":["string","null"]},"id":{"type":"string"},"instance":{"type":"string"},"message":{"type":["string","null"]},"network":{"default":null,"type":["string","null"]},"output":{"anyOf":[{"$ref":"#/$defs/CommandOutput"},{"type":"null"}]},"started":{"format":"uint64","minimum":0,"type":"integer"},"state":{"type":"string"}},"required":["id","instance","action","started","state"],"type":"object"};
const schema138 = {"oneOf":[{"properties":{"commands":{"items":{"$ref":"#/$defs/CommandSpec"},"type":"array"},"kind":{"const":"help","type":"string"}},"required":["kind","commands"],"type":"object"},{"properties":{"channels":{"items":{"$ref":"#/$defs/DirectoryEntry"},"type":"array"},"kind":{"const":"directory","type":"string"}},"required":["kind","channels"],"type":"object"},{"properties":{"channel":{"type":"string"},"expires":{"format":"uint64","minimum":0,"type":"integer"},"kind":{"const":"invitation","type":"string"},"link":{"type":"string"},"localOnly":{"default":false,"type":"boolean"}},"required":["kind","channel","link","expires"],"type":"object"},{"properties":{"kind":{"const":"text","type":"string"},"text":{"type":"string"},"title":{"type":"string"}},"required":["kind","title","text"],"type":"object"},{"properties":{"kind":{"const":"status","type":"string"},"text":{"type":"string"}},"required":["kind","text"],"type":"object"},{"properties":{"conversation":{"type":"string"},"kind":{"const":"close","type":"string"}},"required":["kind","conversation"],"type":"object"}]};
const schema140 = {"properties":{"conversation":{"type":["string","null"]},"joined":{"type":"boolean"},"name":{"type":"string"}},"required":["name","joined"],"type":"object"};

function validate119(data, {instancePath="", parentData, parentDataProperty, rootData=data, dynamicAnchors={}}={}){
let vErrors = null;
let errors = 0;
const evaluated0 = validate119.evaluated;
if(evaluated0.dynamicProps){
evaluated0.props = undefined;
}
if(evaluated0.dynamicItems){
evaluated0.items = undefined;
}
const _errs0 = errors;
let valid0 = false;
let passing0 = null;
const _errs1 = errors;
if(errors === _errs1){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing0;
if(((data.kind === undefined) && (missing0 = "kind")) || ((data.commands === undefined) && (missing0 = "commands"))){
const err0 = {instancePath,schemaPath:"#/oneOf/0/required",keyword:"required",params:{missingProperty: missing0},message:"must have required property '"+missing0+"'"};
if(vErrors === null){
vErrors = [err0];
}
else {
vErrors.push(err0);
}
errors++;
}
else {
if(data.commands !== undefined){
let data0 = data.commands;
const _errs3 = errors;
if(errors === _errs3){
if(Array.isArray(data0)){
var valid2 = true;
const len0 = data0.length;
for(let i0=0; i0<len0; i0++){
let data1 = data0[i0];
const _errs5 = errors;
const _errs6 = errors;
if(errors === _errs6){
if(data1 && typeof data1 == "object" && !Array.isArray(data1)){
let missing1;
if((((((data1.name === undefined) && (missing1 = "name")) || ((data1.usage === undefined) && (missing1 = "usage"))) || ((data1.description === undefined) && (missing1 = "description"))) || ((data1.scope === undefined) && (missing1 = "scope"))) || ((data1.available === undefined) && (missing1 = "available"))){
const err1 = {instancePath:instancePath+"/commands/" + i0,schemaPath:"#/$defs/CommandSpec/required",keyword:"required",params:{missingProperty: missing1},message:"must have required property '"+missing1+"'"};
if(vErrors === null){
vErrors = [err1];
}
else {
vErrors.push(err1);
}
errors++;
}
else {
if(data1.available !== undefined){
const _errs8 = errors;
if(typeof data1.available !== "boolean"){
const err2 = {instancePath:instancePath+"/commands/" + i0+"/available",schemaPath:"#/$defs/CommandSpec/properties/available/type",keyword:"type",params:{type: "boolean"},message:"must be boolean"};
if(vErrors === null){
vErrors = [err2];
}
else {
vErrors.push(err2);
}
errors++;
}
var valid4 = _errs8 === errors;
}
else {
var valid4 = true;
}
if(valid4){
if(data1.capability !== undefined){
let data3 = data1.capability;
const _errs10 = errors;
if((typeof data3 !== "string") && (data3 !== null)){
const err3 = {instancePath:instancePath+"/commands/" + i0+"/capability",schemaPath:"#/$defs/CommandSpec/properties/capability/type",keyword:"type",params:{type: schema132.properties.capability.type},message:"must be string,null"};
if(vErrors === null){
vErrors = [err3];
}
else {
vErrors.push(err3);
}
errors++;
}
var valid4 = _errs10 === errors;
}
else {
var valid4 = true;
}
if(valid4){
if(data1.description !== undefined){
const _errs12 = errors;
if(typeof data1.description !== "string"){
const err4 = {instancePath:instancePath+"/commands/" + i0+"/description",schemaPath:"#/$defs/CommandSpec/properties/description/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err4];
}
else {
vErrors.push(err4);
}
errors++;
}
var valid4 = _errs12 === errors;
}
else {
var valid4 = true;
}
if(valid4){
if(data1.name !== undefined){
const _errs14 = errors;
if(typeof data1.name !== "string"){
const err5 = {instancePath:instancePath+"/commands/" + i0+"/name",schemaPath:"#/$defs/CommandSpec/properties/name/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err5];
}
else {
vErrors.push(err5);
}
errors++;
}
var valid4 = _errs14 === errors;
}
else {
var valid4 = true;
}
if(valid4){
if(data1.scope !== undefined){
const _errs16 = errors;
if(typeof data1.scope !== "string"){
const err6 = {instancePath:instancePath+"/commands/" + i0+"/scope",schemaPath:"#/$defs/CommandSpec/properties/scope/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err6];
}
else {
vErrors.push(err6);
}
errors++;
}
var valid4 = _errs16 === errors;
}
else {
var valid4 = true;
}
if(valid4){
if(data1.usage !== undefined){
const _errs18 = errors;
if(typeof data1.usage !== "string"){
const err7 = {instancePath:instancePath+"/commands/" + i0+"/usage",schemaPath:"#/$defs/CommandSpec/properties/usage/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err7];
}
else {
vErrors.push(err7);
}
errors++;
}
var valid4 = _errs18 === errors;
}
else {
var valid4 = true;
}
}
}
}
}
}
}
}
else {
const err8 = {instancePath:instancePath+"/commands/" + i0,schemaPath:"#/$defs/CommandSpec/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err8];
}
else {
vErrors.push(err8);
}
errors++;
}
}
var valid2 = _errs5 === errors;
if(!valid2){
break;
}
}
}
else {
const err9 = {instancePath:instancePath+"/commands",schemaPath:"#/oneOf/0/properties/commands/type",keyword:"type",params:{type: "array"},message:"must be array"};
if(vErrors === null){
vErrors = [err9];
}
else {
vErrors.push(err9);
}
errors++;
}
}
var valid1 = _errs3 === errors;
}
else {
var valid1 = true;
}
if(valid1){
if(data.kind !== undefined){
let data8 = data.kind;
const _errs20 = errors;
if(typeof data8 !== "string"){
const err10 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/0/properties/kind/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err10];
}
else {
vErrors.push(err10);
}
errors++;
}
if("help" !== data8){
const err11 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/0/properties/kind/const",keyword:"const",params:{allowedValue: "help"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err11];
}
else {
vErrors.push(err11);
}
errors++;
}
var valid1 = _errs20 === errors;
}
else {
var valid1 = true;
}
}
}
}
else {
const err12 = {instancePath,schemaPath:"#/oneOf/0/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err12];
}
else {
vErrors.push(err12);
}
errors++;
}
}
var _valid0 = _errs1 === errors;
if(_valid0){
valid0 = true;
passing0 = 0;
var props0 = {};
props0.commands = true;
props0.kind = true;
}
const _errs22 = errors;
if(errors === _errs22){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing2;
if(((data.kind === undefined) && (missing2 = "kind")) || ((data.channels === undefined) && (missing2 = "channels"))){
const err13 = {instancePath,schemaPath:"#/oneOf/1/required",keyword:"required",params:{missingProperty: missing2},message:"must have required property '"+missing2+"'"};
if(vErrors === null){
vErrors = [err13];
}
else {
vErrors.push(err13);
}
errors++;
}
else {
if(data.channels !== undefined){
let data9 = data.channels;
const _errs24 = errors;
if(errors === _errs24){
if(Array.isArray(data9)){
var valid6 = true;
const len1 = data9.length;
for(let i1=0; i1<len1; i1++){
let data10 = data9[i1];
const _errs26 = errors;
const _errs27 = errors;
if(errors === _errs27){
if(data10 && typeof data10 == "object" && !Array.isArray(data10)){
let missing3;
if(((data10.name === undefined) && (missing3 = "name")) || ((data10.joined === undefined) && (missing3 = "joined"))){
const err14 = {instancePath:instancePath+"/channels/" + i1,schemaPath:"#/$defs/DirectoryEntry/required",keyword:"required",params:{missingProperty: missing3},message:"must have required property '"+missing3+"'"};
if(vErrors === null){
vErrors = [err14];
}
else {
vErrors.push(err14);
}
errors++;
}
else {
if(data10.conversation !== undefined){
let data11 = data10.conversation;
const _errs29 = errors;
if((typeof data11 !== "string") && (data11 !== null)){
const err15 = {instancePath:instancePath+"/channels/" + i1+"/conversation",schemaPath:"#/$defs/DirectoryEntry/properties/conversation/type",keyword:"type",params:{type: schema140.properties.conversation.type},message:"must be string,null"};
if(vErrors === null){
vErrors = [err15];
}
else {
vErrors.push(err15);
}
errors++;
}
var valid8 = _errs29 === errors;
}
else {
var valid8 = true;
}
if(valid8){
if(data10.joined !== undefined){
const _errs31 = errors;
if(typeof data10.joined !== "boolean"){
const err16 = {instancePath:instancePath+"/channels/" + i1+"/joined",schemaPath:"#/$defs/DirectoryEntry/properties/joined/type",keyword:"type",params:{type: "boolean"},message:"must be boolean"};
if(vErrors === null){
vErrors = [err16];
}
else {
vErrors.push(err16);
}
errors++;
}
var valid8 = _errs31 === errors;
}
else {
var valid8 = true;
}
if(valid8){
if(data10.name !== undefined){
const _errs33 = errors;
if(typeof data10.name !== "string"){
const err17 = {instancePath:instancePath+"/channels/" + i1+"/name",schemaPath:"#/$defs/DirectoryEntry/properties/name/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err17];
}
else {
vErrors.push(err17);
}
errors++;
}
var valid8 = _errs33 === errors;
}
else {
var valid8 = true;
}
}
}
}
}
else {
const err18 = {instancePath:instancePath+"/channels/" + i1,schemaPath:"#/$defs/DirectoryEntry/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err18];
}
else {
vErrors.push(err18);
}
errors++;
}
}
var valid6 = _errs26 === errors;
if(!valid6){
break;
}
}
}
else {
const err19 = {instancePath:instancePath+"/channels",schemaPath:"#/oneOf/1/properties/channels/type",keyword:"type",params:{type: "array"},message:"must be array"};
if(vErrors === null){
vErrors = [err19];
}
else {
vErrors.push(err19);
}
errors++;
}
}
var valid5 = _errs24 === errors;
}
else {
var valid5 = true;
}
if(valid5){
if(data.kind !== undefined){
let data14 = data.kind;
const _errs35 = errors;
if(typeof data14 !== "string"){
const err20 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/1/properties/kind/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err20];
}
else {
vErrors.push(err20);
}
errors++;
}
if("directory" !== data14){
const err21 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/1/properties/kind/const",keyword:"const",params:{allowedValue: "directory"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err21];
}
else {
vErrors.push(err21);
}
errors++;
}
var valid5 = _errs35 === errors;
}
else {
var valid5 = true;
}
}
}
}
else {
const err22 = {instancePath,schemaPath:"#/oneOf/1/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err22];
}
else {
vErrors.push(err22);
}
errors++;
}
}
var _valid0 = _errs22 === errors;
if(_valid0 && valid0){
valid0 = false;
passing0 = [passing0, 1];
}
else {
if(_valid0){
valid0 = true;
passing0 = 1;
if(props0 !== true){
props0 = props0 || {};
props0.channels = true;
props0.kind = true;
}
}
const _errs37 = errors;
if(errors === _errs37){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing4;
if(((((data.kind === undefined) && (missing4 = "kind")) || ((data.channel === undefined) && (missing4 = "channel"))) || ((data.link === undefined) && (missing4 = "link"))) || ((data.expires === undefined) && (missing4 = "expires"))){
const err23 = {instancePath,schemaPath:"#/oneOf/2/required",keyword:"required",params:{missingProperty: missing4},message:"must have required property '"+missing4+"'"};
if(vErrors === null){
vErrors = [err23];
}
else {
vErrors.push(err23);
}
errors++;
}
else {
if(data.channel !== undefined){
const _errs39 = errors;
if(typeof data.channel !== "string"){
const err24 = {instancePath:instancePath+"/channel",schemaPath:"#/oneOf/2/properties/channel/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err24];
}
else {
vErrors.push(err24);
}
errors++;
}
var valid9 = _errs39 === errors;
}
else {
var valid9 = true;
}
if(valid9){
if(data.expires !== undefined){
let data16 = data.expires;
const _errs41 = errors;
if(!(((typeof data16 == "number") && (!(data16 % 1) && !isNaN(data16))) && (isFinite(data16)))){
const err25 = {instancePath:instancePath+"/expires",schemaPath:"#/oneOf/2/properties/expires/type",keyword:"type",params:{type: "integer"},message:"must be integer"};
if(vErrors === null){
vErrors = [err25];
}
else {
vErrors.push(err25);
}
errors++;
}
if(errors === _errs41){
if((typeof data16 == "number") && (isFinite(data16))){
if(data16 < 0 || isNaN(data16)){
const err26 = {instancePath:instancePath+"/expires",schemaPath:"#/oneOf/2/properties/expires/minimum",keyword:"minimum",params:{comparison: ">=", limit: 0},message:"must be >= 0"};
if(vErrors === null){
vErrors = [err26];
}
else {
vErrors.push(err26);
}
errors++;
}
}
}
var valid9 = _errs41 === errors;
}
else {
var valid9 = true;
}
if(valid9){
if(data.kind !== undefined){
let data17 = data.kind;
const _errs43 = errors;
if(typeof data17 !== "string"){
const err27 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/2/properties/kind/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err27];
}
else {
vErrors.push(err27);
}
errors++;
}
if("invitation" !== data17){
const err28 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/2/properties/kind/const",keyword:"const",params:{allowedValue: "invitation"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err28];
}
else {
vErrors.push(err28);
}
errors++;
}
var valid9 = _errs43 === errors;
}
else {
var valid9 = true;
}
if(valid9){
if(data.link !== undefined){
const _errs45 = errors;
if(typeof data.link !== "string"){
const err29 = {instancePath:instancePath+"/link",schemaPath:"#/oneOf/2/properties/link/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err29];
}
else {
vErrors.push(err29);
}
errors++;
}
var valid9 = _errs45 === errors;
}
else {
var valid9 = true;
}
if(valid9){
if(data.localOnly !== undefined){
const _errs47 = errors;
if(typeof data.localOnly !== "boolean"){
const err30 = {instancePath:instancePath+"/localOnly",schemaPath:"#/oneOf/2/properties/localOnly/type",keyword:"type",params:{type: "boolean"},message:"must be boolean"};
if(vErrors === null){
vErrors = [err30];
}
else {
vErrors.push(err30);
}
errors++;
}
var valid9 = _errs47 === errors;
}
else {
var valid9 = true;
}
}
}
}
}
}
}
else {
const err31 = {instancePath,schemaPath:"#/oneOf/2/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err31];
}
else {
vErrors.push(err31);
}
errors++;
}
}
var _valid0 = _errs37 === errors;
if(_valid0 && valid0){
valid0 = false;
passing0 = [passing0, 2];
}
else {
if(_valid0){
valid0 = true;
passing0 = 2;
if(props0 !== true){
props0 = props0 || {};
props0.channel = true;
props0.expires = true;
props0.kind = true;
props0.link = true;
props0.localOnly = true;
}
}
const _errs49 = errors;
if(errors === _errs49){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing5;
if((((data.kind === undefined) && (missing5 = "kind")) || ((data.title === undefined) && (missing5 = "title"))) || ((data.text === undefined) && (missing5 = "text"))){
const err32 = {instancePath,schemaPath:"#/oneOf/3/required",keyword:"required",params:{missingProperty: missing5},message:"must have required property '"+missing5+"'"};
if(vErrors === null){
vErrors = [err32];
}
else {
vErrors.push(err32);
}
errors++;
}
else {
if(data.kind !== undefined){
let data20 = data.kind;
const _errs51 = errors;
if(typeof data20 !== "string"){
const err33 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/3/properties/kind/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err33];
}
else {
vErrors.push(err33);
}
errors++;
}
if("text" !== data20){
const err34 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/3/properties/kind/const",keyword:"const",params:{allowedValue: "text"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err34];
}
else {
vErrors.push(err34);
}
errors++;
}
var valid10 = _errs51 === errors;
}
else {
var valid10 = true;
}
if(valid10){
if(data.text !== undefined){
const _errs53 = errors;
if(typeof data.text !== "string"){
const err35 = {instancePath:instancePath+"/text",schemaPath:"#/oneOf/3/properties/text/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err35];
}
else {
vErrors.push(err35);
}
errors++;
}
var valid10 = _errs53 === errors;
}
else {
var valid10 = true;
}
if(valid10){
if(data.title !== undefined){
const _errs55 = errors;
if(typeof data.title !== "string"){
const err36 = {instancePath:instancePath+"/title",schemaPath:"#/oneOf/3/properties/title/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err36];
}
else {
vErrors.push(err36);
}
errors++;
}
var valid10 = _errs55 === errors;
}
else {
var valid10 = true;
}
}
}
}
}
else {
const err37 = {instancePath,schemaPath:"#/oneOf/3/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err37];
}
else {
vErrors.push(err37);
}
errors++;
}
}
var _valid0 = _errs49 === errors;
if(_valid0 && valid0){
valid0 = false;
passing0 = [passing0, 3];
}
else {
if(_valid0){
valid0 = true;
passing0 = 3;
if(props0 !== true){
props0 = props0 || {};
props0.kind = true;
props0.text = true;
props0.title = true;
}
}
const _errs57 = errors;
if(errors === _errs57){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing6;
if(((data.kind === undefined) && (missing6 = "kind")) || ((data.text === undefined) && (missing6 = "text"))){
const err38 = {instancePath,schemaPath:"#/oneOf/4/required",keyword:"required",params:{missingProperty: missing6},message:"must have required property '"+missing6+"'"};
if(vErrors === null){
vErrors = [err38];
}
else {
vErrors.push(err38);
}
errors++;
}
else {
if(data.kind !== undefined){
let data23 = data.kind;
const _errs59 = errors;
if(typeof data23 !== "string"){
const err39 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/4/properties/kind/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err39];
}
else {
vErrors.push(err39);
}
errors++;
}
if("status" !== data23){
const err40 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/4/properties/kind/const",keyword:"const",params:{allowedValue: "status"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err40];
}
else {
vErrors.push(err40);
}
errors++;
}
var valid11 = _errs59 === errors;
}
else {
var valid11 = true;
}
if(valid11){
if(data.text !== undefined){
const _errs61 = errors;
if(typeof data.text !== "string"){
const err41 = {instancePath:instancePath+"/text",schemaPath:"#/oneOf/4/properties/text/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err41];
}
else {
vErrors.push(err41);
}
errors++;
}
var valid11 = _errs61 === errors;
}
else {
var valid11 = true;
}
}
}
}
else {
const err42 = {instancePath,schemaPath:"#/oneOf/4/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err42];
}
else {
vErrors.push(err42);
}
errors++;
}
}
var _valid0 = _errs57 === errors;
if(_valid0 && valid0){
valid0 = false;
passing0 = [passing0, 4];
}
else {
if(_valid0){
valid0 = true;
passing0 = 4;
if(props0 !== true){
props0 = props0 || {};
props0.kind = true;
props0.text = true;
}
}
const _errs63 = errors;
if(errors === _errs63){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing7;
if(((data.kind === undefined) && (missing7 = "kind")) || ((data.conversation === undefined) && (missing7 = "conversation"))){
const err43 = {instancePath,schemaPath:"#/oneOf/5/required",keyword:"required",params:{missingProperty: missing7},message:"must have required property '"+missing7+"'"};
if(vErrors === null){
vErrors = [err43];
}
else {
vErrors.push(err43);
}
errors++;
}
else {
if(data.conversation !== undefined){
const _errs65 = errors;
if(typeof data.conversation !== "string"){
const err44 = {instancePath:instancePath+"/conversation",schemaPath:"#/oneOf/5/properties/conversation/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err44];
}
else {
vErrors.push(err44);
}
errors++;
}
var valid12 = _errs65 === errors;
}
else {
var valid12 = true;
}
if(valid12){
if(data.kind !== undefined){
let data26 = data.kind;
const _errs67 = errors;
if(typeof data26 !== "string"){
const err45 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/5/properties/kind/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err45];
}
else {
vErrors.push(err45);
}
errors++;
}
if("close" !== data26){
const err46 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/5/properties/kind/const",keyword:"const",params:{allowedValue: "close"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err46];
}
else {
vErrors.push(err46);
}
errors++;
}
var valid12 = _errs67 === errors;
}
else {
var valid12 = true;
}
}
}
}
else {
const err47 = {instancePath,schemaPath:"#/oneOf/5/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err47];
}
else {
vErrors.push(err47);
}
errors++;
}
}
var _valid0 = _errs63 === errors;
if(_valid0 && valid0){
valid0 = false;
passing0 = [passing0, 5];
}
else {
if(_valid0){
valid0 = true;
passing0 = 5;
if(props0 !== true){
props0 = props0 || {};
props0.conversation = true;
props0.kind = true;
}
}
}
}
}
}
}
if(!valid0){
const err48 = {instancePath,schemaPath:"#/oneOf",keyword:"oneOf",params:{passingSchemas: passing0},message:"must match exactly one schema in oneOf"};
if(vErrors === null){
vErrors = [err48];
}
else {
vErrors.push(err48);
}
errors++;
validate119.errors = vErrors;
return false;
}
else {
errors = _errs0;
if(vErrors !== null){
if(_errs0){
vErrors.length = _errs0;
}
else {
vErrors = null;
}
}
}
validate119.errors = vErrors;
evaluated0.props = props0;
return errors === 0;
}
validate119.evaluated = {"dynamicProps":true,"dynamicItems":false};


function validate118(data, {instancePath="", parentData, parentDataProperty, rootData=data, dynamicAnchors={}}={}){
let vErrors = null;
let errors = 0;
const evaluated0 = validate118.evaluated;
if(evaluated0.dynamicProps){
evaluated0.props = undefined;
}
if(evaluated0.dynamicItems){
evaluated0.items = undefined;
}
if(errors === 0){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing0;
if((((((data.id === undefined) && (missing0 = "id")) || ((data.instance === undefined) && (missing0 = "instance"))) || ((data.action === undefined) && (missing0 = "action"))) || ((data.started === undefined) && (missing0 = "started"))) || ((data.state === undefined) && (missing0 = "state"))){
validate118.errors = [{instancePath,schemaPath:"#/required",keyword:"required",params:{missingProperty: missing0},message:"must have required property '"+missing0+"'"}];
return false;
}
else {
if(data.action !== undefined){
const _errs1 = errors;
if(typeof data.action !== "string"){
validate118.errors = [{instancePath:instancePath+"/action",schemaPath:"#/properties/action/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs1 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.conversation !== undefined){
let data1 = data.conversation;
const _errs3 = errors;
if((typeof data1 !== "string") && (data1 !== null)){
validate118.errors = [{instancePath:instancePath+"/conversation",schemaPath:"#/properties/conversation/type",keyword:"type",params:{type: schema137.properties.conversation.type},message:"must be string,null"}];
return false;
}
var valid0 = _errs3 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.id !== undefined){
const _errs5 = errors;
if(typeof data.id !== "string"){
validate118.errors = [{instancePath:instancePath+"/id",schemaPath:"#/properties/id/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs5 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.instance !== undefined){
const _errs7 = errors;
if(typeof data.instance !== "string"){
validate118.errors = [{instancePath:instancePath+"/instance",schemaPath:"#/properties/instance/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs7 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.message !== undefined){
let data4 = data.message;
const _errs9 = errors;
if((typeof data4 !== "string") && (data4 !== null)){
validate118.errors = [{instancePath:instancePath+"/message",schemaPath:"#/properties/message/type",keyword:"type",params:{type: schema137.properties.message.type},message:"must be string,null"}];
return false;
}
var valid0 = _errs9 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.network !== undefined){
let data5 = data.network;
const _errs11 = errors;
if((typeof data5 !== "string") && (data5 !== null)){
validate118.errors = [{instancePath:instancePath+"/network",schemaPath:"#/properties/network/type",keyword:"type",params:{type: schema137.properties.network.type},message:"must be string,null"}];
return false;
}
var valid0 = _errs11 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.output !== undefined){
let data6 = data.output;
const _errs13 = errors;
const _errs14 = errors;
let valid1 = false;
const _errs15 = errors;
if(!(validate119(data6, {instancePath:instancePath+"/output",parentData:data,parentDataProperty:"output",rootData,dynamicAnchors}))){
vErrors = vErrors === null ? validate119.errors : vErrors.concat(validate119.errors);
errors = vErrors.length;
}
var _valid0 = _errs15 === errors;
valid1 = valid1 || _valid0;
const _errs16 = errors;
if(data6 !== null){
const err0 = {instancePath:instancePath+"/output",schemaPath:"#/properties/output/anyOf/1/type",keyword:"type",params:{type: "null"},message:"must be null"};
if(vErrors === null){
vErrors = [err0];
}
else {
vErrors.push(err0);
}
errors++;
}
var _valid0 = _errs16 === errors;
valid1 = valid1 || _valid0;
if(!valid1){
const err1 = {instancePath:instancePath+"/output",schemaPath:"#/properties/output/anyOf",keyword:"anyOf",params:{},message:"must match a schema in anyOf"};
if(vErrors === null){
vErrors = [err1];
}
else {
vErrors.push(err1);
}
errors++;
validate118.errors = vErrors;
return false;
}
else {
errors = _errs14;
if(vErrors !== null){
if(_errs14){
vErrors.length = _errs14;
}
else {
vErrors = null;
}
}
}
var valid0 = _errs13 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.started !== undefined){
let data7 = data.started;
const _errs18 = errors;
if(!(((typeof data7 == "number") && (!(data7 % 1) && !isNaN(data7))) && (isFinite(data7)))){
validate118.errors = [{instancePath:instancePath+"/started",schemaPath:"#/properties/started/type",keyword:"type",params:{type: "integer"},message:"must be integer"}];
return false;
}
if(errors === _errs18){
if((typeof data7 == "number") && (isFinite(data7))){
if(data7 < 0 || isNaN(data7)){
validate118.errors = [{instancePath:instancePath+"/started",schemaPath:"#/properties/started/minimum",keyword:"minimum",params:{comparison: ">=", limit: 0},message:"must be >= 0"}];
return false;
}
}
}
var valid0 = _errs18 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.state !== undefined){
const _errs20 = errors;
if(typeof data.state !== "string"){
validate118.errors = [{instancePath:instancePath+"/state",schemaPath:"#/properties/state/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs20 === errors;
}
else {
var valid0 = true;
}
}
}
}
}
}
}
}
}
}
}
else {
validate118.errors = [{instancePath,schemaPath:"#/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
validate118.errors = vErrors;
return errors === 0;
}
validate118.evaluated = {"props":{"action":true,"conversation":true,"id":true,"instance":true,"message":true,"network":true,"output":true,"started":true,"state":true},"dynamicProps":false,"dynamicItems":false};


function validate115(data, {instancePath="", parentData, parentDataProperty, rootData=data, dynamicAnchors={}}={}){
let vErrors = null;
let errors = 0;
const evaluated0 = validate115.evaluated;
if(evaluated0.dynamicProps){
evaluated0.props = undefined;
}
if(evaluated0.dynamicItems){
evaluated0.items = undefined;
}
if(errors === 0){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing0;
if((((((data.instance === undefined) && (missing0 = "instance")) || ((data.revision === undefined) && (missing0 = "revision"))) || ((data.conversations === undefined) && (missing0 = "conversations"))) || ((data.commandHistory === undefined) && (missing0 = "commandHistory"))) || ((data.inputHistory === undefined) && (missing0 = "inputHistory"))){
validate115.errors = [{instancePath,schemaPath:"#/required",keyword:"required",params:{missingProperty: missing0},message:"must have required property '"+missing0+"'"}];
return false;
}
else {
if(data.activity !== undefined){
let data0 = data.activity;
const _errs1 = errors;
if((!(Array.isArray(data0))) && (data0 !== null)){
validate115.errors = [{instancePath:instancePath+"/activity",schemaPath:"#/properties/activity/type",keyword:"type",params:{type: schema129.properties.activity.type},message:"must be array,null"}];
return false;
}
if(errors === _errs1){
if(Array.isArray(data0)){
var valid1 = true;
const len0 = data0.length;
for(let i0=0; i0<len0; i0++){
let data1 = data0[i0];
const _errs3 = errors;
const _errs4 = errors;
if(errors === _errs4){
if(data1 && typeof data1 == "object" && !Array.isArray(data1)){
let missing1;
if((((((data1.id === undefined) && (missing1 = "id")) || ((data1.conversation === undefined) && (missing1 = "conversation"))) || ((data1.kind === undefined) && (missing1 = "kind"))) || ((data1.text === undefined) && (missing1 = "text"))) || ((data1.timestamp === undefined) && (missing1 = "timestamp"))){
validate115.errors = [{instancePath:instancePath+"/activity/" + i0,schemaPath:"#/$defs/Activity/required",keyword:"required",params:{missingProperty: missing1},message:"must have required property '"+missing1+"'"}];
return false;
}
else {
if(data1.conversation !== undefined){
const _errs6 = errors;
if(typeof data1.conversation !== "string"){
validate115.errors = [{instancePath:instancePath+"/activity/" + i0+"/conversation",schemaPath:"#/$defs/Activity/properties/conversation/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid3 = _errs6 === errors;
}
else {
var valid3 = true;
}
if(valid3){
if(data1.id !== undefined){
const _errs8 = errors;
if(typeof data1.id !== "string"){
validate115.errors = [{instancePath:instancePath+"/activity/" + i0+"/id",schemaPath:"#/$defs/Activity/properties/id/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid3 = _errs8 === errors;
}
else {
var valid3 = true;
}
if(valid3){
if(data1.kind !== undefined){
const _errs10 = errors;
if(typeof data1.kind !== "string"){
validate115.errors = [{instancePath:instancePath+"/activity/" + i0+"/kind",schemaPath:"#/$defs/Activity/properties/kind/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid3 = _errs10 === errors;
}
else {
var valid3 = true;
}
if(valid3){
if(data1.text !== undefined){
const _errs12 = errors;
if(typeof data1.text !== "string"){
validate115.errors = [{instancePath:instancePath+"/activity/" + i0+"/text",schemaPath:"#/$defs/Activity/properties/text/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid3 = _errs12 === errors;
}
else {
var valid3 = true;
}
if(valid3){
if(data1.timestamp !== undefined){
let data6 = data1.timestamp;
const _errs14 = errors;
if(!(((typeof data6 == "number") && (!(data6 % 1) && !isNaN(data6))) && (isFinite(data6)))){
validate115.errors = [{instancePath:instancePath+"/activity/" + i0+"/timestamp",schemaPath:"#/$defs/Activity/properties/timestamp/type",keyword:"type",params:{type: "integer"},message:"must be integer"}];
return false;
}
if(errors === _errs14){
if((typeof data6 == "number") && (isFinite(data6))){
if(data6 < 0 || isNaN(data6)){
validate115.errors = [{instancePath:instancePath+"/activity/" + i0+"/timestamp",schemaPath:"#/$defs/Activity/properties/timestamp/minimum",keyword:"minimum",params:{comparison: ">=", limit: 0},message:"must be >= 0"}];
return false;
}
}
}
var valid3 = _errs14 === errors;
}
else {
var valid3 = true;
}
}
}
}
}
}
}
else {
validate115.errors = [{instancePath:instancePath+"/activity/" + i0,schemaPath:"#/$defs/Activity/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
var valid1 = _errs3 === errors;
if(!valid1){
break;
}
}
}
}
var valid0 = _errs1 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.commandHistory !== undefined){
let data7 = data.commandHistory;
const _errs16 = errors;
if(errors === _errs16){
if(Array.isArray(data7)){
var valid4 = true;
const len1 = data7.length;
for(let i1=0; i1<len1; i1++){
const _errs18 = errors;
if(typeof data7[i1] !== "string"){
validate115.errors = [{instancePath:instancePath+"/commandHistory/" + i1,schemaPath:"#/properties/commandHistory/items/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid4 = _errs18 === errors;
if(!valid4){
break;
}
}
}
else {
validate115.errors = [{instancePath:instancePath+"/commandHistory",schemaPath:"#/properties/commandHistory/type",keyword:"type",params:{type: "array"},message:"must be array"}];
return false;
}
}
var valid0 = _errs16 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.conversations !== undefined){
let data9 = data.conversations;
const _errs20 = errors;
if(errors === _errs20){
if(Array.isArray(data9)){
var valid5 = true;
const len2 = data9.length;
for(let i2=0; i2<len2; i2++){
const _errs22 = errors;
if(!(validate116(data9[i2], {instancePath:instancePath+"/conversations/" + i2,parentData:data9,parentDataProperty:i2,rootData,dynamicAnchors}))){
vErrors = vErrors === null ? validate116.errors : vErrors.concat(validate116.errors);
errors = vErrors.length;
}
var valid5 = _errs22 === errors;
if(!valid5){
break;
}
}
}
else {
validate115.errors = [{instancePath:instancePath+"/conversations",schemaPath:"#/properties/conversations/type",keyword:"type",params:{type: "array"},message:"must be array"}];
return false;
}
}
var valid0 = _errs20 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.inputHistory !== undefined){
let data11 = data.inputHistory;
const _errs23 = errors;
if(errors === _errs23){
if(Array.isArray(data11)){
var valid6 = true;
const len3 = data11.length;
for(let i3=0; i3<len3; i3++){
let data12 = data11[i3];
const _errs25 = errors;
const _errs26 = errors;
if(errors === _errs26){
if(data12 && typeof data12 == "object" && !Array.isArray(data12)){
let missing2;
if((data12.text === undefined) && (missing2 = "text")){
validate115.errors = [{instancePath:instancePath+"/inputHistory/" + i3,schemaPath:"#/$defs/InputHistoryEntry/required",keyword:"required",params:{missingProperty: missing2},message:"must have required property '"+missing2+"'"}];
return false;
}
else {
if(data12.conversation !== undefined){
let data13 = data12.conversation;
const _errs28 = errors;
if((typeof data13 !== "string") && (data13 !== null)){
validate115.errors = [{instancePath:instancePath+"/inputHistory/" + i3+"/conversation",schemaPath:"#/$defs/InputHistoryEntry/properties/conversation/type",keyword:"type",params:{type: schema135.properties.conversation.type},message:"must be string,null"}];
return false;
}
var valid8 = _errs28 === errors;
}
else {
var valid8 = true;
}
if(valid8){
if(data12.text !== undefined){
const _errs30 = errors;
if(typeof data12.text !== "string"){
validate115.errors = [{instancePath:instancePath+"/inputHistory/" + i3+"/text",schemaPath:"#/$defs/InputHistoryEntry/properties/text/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid8 = _errs30 === errors;
}
else {
var valid8 = true;
}
}
}
}
else {
validate115.errors = [{instancePath:instancePath+"/inputHistory/" + i3,schemaPath:"#/$defs/InputHistoryEntry/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
var valid6 = _errs25 === errors;
if(!valid6){
break;
}
}
}
else {
validate115.errors = [{instancePath:instancePath+"/inputHistory",schemaPath:"#/properties/inputHistory/type",keyword:"type",params:{type: "array"},message:"must be array"}];
return false;
}
}
var valid0 = _errs23 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.instance !== undefined){
let data15 = data.instance;
const _errs32 = errors;
const _errs33 = errors;
if(errors === _errs33){
if(data15 && typeof data15 == "object" && !Array.isArray(data15)){
let missing3;
if((((((((((data15.id === undefined) && (missing3 = "id")) || ((data15.label === undefined) && (missing3 = "label"))) || ((data15.bootId === undefined) && (missing3 = "bootId"))) || ((data15.locked === undefined) && (missing3 = "locked"))) || ((data15.protocolLocked === undefined) && (missing3 = "protocolLocked"))) || ((data15.profileExists === undefined) && (missing3 = "profileExists"))) || ((data15.archiveExists === undefined) && (missing3 = "archiveExists"))) || ((data15.safetyNumber === undefined) && (missing3 = "safetyNumber"))) || ((data15.capabilities === undefined) && (missing3 = "capabilities"))){
validate115.errors = [{instancePath:instancePath+"/instance",schemaPath:"#/$defs/InstanceInfo/required",keyword:"required",params:{missingProperty: missing3},message:"must have required property '"+missing3+"'"}];
return false;
}
else {
if(data15.archiveExists !== undefined){
const _errs35 = errors;
if(typeof data15.archiveExists !== "boolean"){
validate115.errors = [{instancePath:instancePath+"/instance/archiveExists",schemaPath:"#/$defs/InstanceInfo/properties/archiveExists/type",keyword:"type",params:{type: "boolean"},message:"must be boolean"}];
return false;
}
var valid10 = _errs35 === errors;
}
else {
var valid10 = true;
}
if(valid10){
if(data15.bootId !== undefined){
const _errs37 = errors;
if(typeof data15.bootId !== "string"){
validate115.errors = [{instancePath:instancePath+"/instance/bootId",schemaPath:"#/$defs/InstanceInfo/properties/bootId/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid10 = _errs37 === errors;
}
else {
var valid10 = true;
}
if(valid10){
if(data15.capabilities !== undefined){
let data18 = data15.capabilities;
const _errs39 = errors;
if(errors === _errs39){
if(Array.isArray(data18)){
var valid11 = true;
const len4 = data18.length;
for(let i4=0; i4<len4; i4++){
const _errs41 = errors;
if(typeof data18[i4] !== "string"){
validate115.errors = [{instancePath:instancePath+"/instance/capabilities/" + i4,schemaPath:"#/$defs/InstanceInfo/properties/capabilities/items/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid11 = _errs41 === errors;
if(!valid11){
break;
}
}
}
else {
validate115.errors = [{instancePath:instancePath+"/instance/capabilities",schemaPath:"#/$defs/InstanceInfo/properties/capabilities/type",keyword:"type",params:{type: "array"},message:"must be array"}];
return false;
}
}
var valid10 = _errs39 === errors;
}
else {
var valid10 = true;
}
if(valid10){
if(data15.id !== undefined){
const _errs43 = errors;
if(typeof data15.id !== "string"){
validate115.errors = [{instancePath:instancePath+"/instance/id",schemaPath:"#/$defs/InstanceInfo/properties/id/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid10 = _errs43 === errors;
}
else {
var valid10 = true;
}
if(valid10){
if(data15.label !== undefined){
const _errs45 = errors;
if(typeof data15.label !== "string"){
validate115.errors = [{instancePath:instancePath+"/instance/label",schemaPath:"#/$defs/InstanceInfo/properties/label/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid10 = _errs45 === errors;
}
else {
var valid10 = true;
}
if(valid10){
if(data15.locked !== undefined){
const _errs47 = errors;
if(typeof data15.locked !== "boolean"){
validate115.errors = [{instancePath:instancePath+"/instance/locked",schemaPath:"#/$defs/InstanceInfo/properties/locked/type",keyword:"type",params:{type: "boolean"},message:"must be boolean"}];
return false;
}
var valid10 = _errs47 === errors;
}
else {
var valid10 = true;
}
if(valid10){
if(data15.profileExists !== undefined){
const _errs49 = errors;
if(typeof data15.profileExists !== "boolean"){
validate115.errors = [{instancePath:instancePath+"/instance/profileExists",schemaPath:"#/$defs/InstanceInfo/properties/profileExists/type",keyword:"type",params:{type: "boolean"},message:"must be boolean"}];
return false;
}
var valid10 = _errs49 === errors;
}
else {
var valid10 = true;
}
if(valid10){
if(data15.protocolLocked !== undefined){
const _errs51 = errors;
if(typeof data15.protocolLocked !== "boolean"){
validate115.errors = [{instancePath:instancePath+"/instance/protocolLocked",schemaPath:"#/$defs/InstanceInfo/properties/protocolLocked/type",keyword:"type",params:{type: "boolean"},message:"must be boolean"}];
return false;
}
var valid10 = _errs51 === errors;
}
else {
var valid10 = true;
}
if(valid10){
if(data15.safetyNumber !== undefined){
const _errs53 = errors;
if(typeof data15.safetyNumber !== "string"){
validate115.errors = [{instancePath:instancePath+"/instance/safetyNumber",schemaPath:"#/$defs/InstanceInfo/properties/safetyNumber/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid10 = _errs53 === errors;
}
else {
var valid10 = true;
}
}
}
}
}
}
}
}
}
}
}
else {
validate115.errors = [{instancePath:instancePath+"/instance",schemaPath:"#/$defs/InstanceInfo/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
var valid0 = _errs32 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.operations !== undefined){
let data26 = data.operations;
const _errs55 = errors;
if((!(Array.isArray(data26))) && (data26 !== null)){
validate115.errors = [{instancePath:instancePath+"/operations",schemaPath:"#/properties/operations/type",keyword:"type",params:{type: schema129.properties.operations.type},message:"must be array,null"}];
return false;
}
if(errors === _errs55){
if(Array.isArray(data26)){
var valid12 = true;
const len5 = data26.length;
for(let i5=0; i5<len5; i5++){
const _errs57 = errors;
if(!(validate118(data26[i5], {instancePath:instancePath+"/operations/" + i5,parentData:data26,parentDataProperty:i5,rootData,dynamicAnchors}))){
vErrors = vErrors === null ? validate118.errors : vErrors.concat(validate118.errors);
errors = vErrors.length;
}
var valid12 = _errs57 === errors;
if(!valid12){
break;
}
}
}
}
var valid0 = _errs55 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.presenceEnabled !== undefined){
let data28 = data.presenceEnabled;
const _errs58 = errors;
if((typeof data28 !== "boolean") && (data28 !== null)){
validate115.errors = [{instancePath:instancePath+"/presenceEnabled",schemaPath:"#/properties/presenceEnabled/type",keyword:"type",params:{type: schema129.properties.presenceEnabled.type},message:"must be boolean,null"}];
return false;
}
var valid0 = _errs58 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.providerErrors !== undefined){
let data29 = data.providerErrors;
const _errs60 = errors;
if(errors === _errs60){
if(Array.isArray(data29)){
var valid13 = true;
const len6 = data29.length;
for(let i6=0; i6<len6; i6++){
let data30 = data29[i6];
const _errs62 = errors;
const _errs63 = errors;
if(errors === _errs63){
if(data30 && typeof data30 == "object" && !Array.isArray(data30)){
let missing4;
if(((((data30.id === undefined) && (missing4 = "id")) || ((data30.code === undefined) && (missing4 = "code"))) || ((data30.message === undefined) && (missing4 = "message"))) || ((data30.retryable === undefined) && (missing4 = "retryable"))){
validate115.errors = [{instancePath:instancePath+"/providerErrors/" + i6,schemaPath:"#/$defs/ProviderStatus/required",keyword:"required",params:{missingProperty: missing4},message:"must have required property '"+missing4+"'"}];
return false;
}
else {
if(data30.code !== undefined){
const _errs65 = errors;
if(typeof data30.code !== "string"){
validate115.errors = [{instancePath:instancePath+"/providerErrors/" + i6+"/code",schemaPath:"#/$defs/ProviderStatus/properties/code/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid15 = _errs65 === errors;
}
else {
var valid15 = true;
}
if(valid15){
if(data30.id !== undefined){
const _errs67 = errors;
if(typeof data30.id !== "string"){
validate115.errors = [{instancePath:instancePath+"/providerErrors/" + i6+"/id",schemaPath:"#/$defs/ProviderStatus/properties/id/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid15 = _errs67 === errors;
}
else {
var valid15 = true;
}
if(valid15){
if(data30.message !== undefined){
const _errs69 = errors;
if(typeof data30.message !== "string"){
validate115.errors = [{instancePath:instancePath+"/providerErrors/" + i6+"/message",schemaPath:"#/$defs/ProviderStatus/properties/message/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid15 = _errs69 === errors;
}
else {
var valid15 = true;
}
if(valid15){
if(data30.retryable !== undefined){
const _errs71 = errors;
if(typeof data30.retryable !== "boolean"){
validate115.errors = [{instancePath:instancePath+"/providerErrors/" + i6+"/retryable",schemaPath:"#/$defs/ProviderStatus/properties/retryable/type",keyword:"type",params:{type: "boolean"},message:"must be boolean"}];
return false;
}
var valid15 = _errs71 === errors;
}
else {
var valid15 = true;
}
}
}
}
}
}
else {
validate115.errors = [{instancePath:instancePath+"/providerErrors/" + i6,schemaPath:"#/$defs/ProviderStatus/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
var valid13 = _errs62 === errors;
if(!valid13){
break;
}
}
}
else {
validate115.errors = [{instancePath:instancePath+"/providerErrors",schemaPath:"#/properties/providerErrors/type",keyword:"type",params:{type: "array"},message:"must be array"}];
return false;
}
}
var valid0 = _errs60 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.revision !== undefined){
const _errs73 = errors;
if(typeof data.revision !== "string"){
validate115.errors = [{instancePath:instancePath+"/revision",schemaPath:"#/properties/revision/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs73 === errors;
}
else {
var valid0 = true;
}
}
}
}
}
}
}
}
}
}
}
else {
validate115.errors = [{instancePath,schemaPath:"#/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
validate115.errors = vErrors;
return errors === 0;
}
validate115.evaluated = {"props":{"activity":true,"commandHistory":true,"conversations":true,"inputHistory":true,"instance":true,"operations":true,"presenceEnabled":true,"providerErrors":true,"revision":true},"dynamicProps":false,"dynamicItems":false};

export const disconnect_error = validate122;
const schema142 = {"$schema":"https://json-schema.org/draft/2020-12/schema","additionalProperties":false,"properties":{"code":{"type":"string"},"message":{"type":"string"}},"required":["code","message"],"title":"ChatError","type":"object"};

function validate122(data, {instancePath="", parentData, parentDataProperty, rootData=data, dynamicAnchors={}}={}){
let vErrors = null;
let errors = 0;
const evaluated0 = validate122.evaluated;
if(evaluated0.dynamicProps){
evaluated0.props = undefined;
}
if(evaluated0.dynamicItems){
evaluated0.items = undefined;
}
if(errors === 0){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing0;
if(((data.code === undefined) && (missing0 = "code")) || ((data.message === undefined) && (missing0 = "message"))){
validate122.errors = [{instancePath,schemaPath:"#/required",keyword:"required",params:{missingProperty: missing0},message:"must have required property '"+missing0+"'"}];
return false;
}
else {
const _errs1 = errors;
for(const key0 in data){
if(!((key0 === "code") || (key0 === "message"))){
validate122.errors = [{instancePath,schemaPath:"#/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key0},message:"must NOT have additional properties"}];
return false;
break;
}
}
if(_errs1 === errors){
if(data.code !== undefined){
const _errs2 = errors;
if(typeof data.code !== "string"){
validate122.errors = [{instancePath:instancePath+"/code",schemaPath:"#/properties/code/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs2 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.message !== undefined){
const _errs4 = errors;
if(typeof data.message !== "string"){
validate122.errors = [{instancePath:instancePath+"/message",schemaPath:"#/properties/message/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs4 === errors;
}
else {
var valid0 = true;
}
}
}
}
}
else {
validate122.errors = [{instancePath,schemaPath:"#/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
validate122.errors = vErrors;
return errors === 0;
}
validate122.evaluated = {"props":true,"dynamicProps":false,"dynamicItems":false};

export const snapshot_args = validate123;
const schema143 = {"$schema":"https://json-schema.org/draft/2020-12/schema","additionalProperties":false,"title":"ChatSnapshotArgs","type":"object"};

function validate123(data, {instancePath="", parentData, parentDataProperty, rootData=data, dynamicAnchors={}}={}){
let vErrors = null;
let errors = 0;
const evaluated0 = validate123.evaluated;
if(evaluated0.dynamicProps){
evaluated0.props = undefined;
}
if(evaluated0.dynamicItems){
evaluated0.items = undefined;
}
if(errors === 0){
if(data && typeof data == "object" && !Array.isArray(data)){
for(const key0 in data){
validate123.errors = [{instancePath,schemaPath:"#/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key0},message:"must NOT have additional properties"}];
return false;
break;
}
}
else {
validate123.errors = [{instancePath,schemaPath:"#/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
validate123.errors = vErrors;
return errors === 0;
}
validate123.evaluated = {"props":true,"dynamicProps":false,"dynamicItems":false};

export const snapshot_output = validate124;
const schema144 = {"$defs":{"Activity":{"description":"Authenticated state changes observed by this profile, retained before publication.","properties":{"conversation":{"type":"string"},"id":{"type":"string"},"kind":{"type":"string"},"text":{"type":"string"},"timestamp":{"format":"uint64","minimum":0,"type":"integer"}},"required":["id","conversation","kind","text","timestamp"],"type":"object"},"CommandOutput":{"oneOf":[{"properties":{"commands":{"items":{"$ref":"#/$defs/CommandSpec"},"type":"array"},"kind":{"const":"help","type":"string"}},"required":["kind","commands"],"type":"object"},{"properties":{"channels":{"items":{"$ref":"#/$defs/DirectoryEntry"},"type":"array"},"kind":{"const":"directory","type":"string"}},"required":["kind","channels"],"type":"object"},{"properties":{"channel":{"type":"string"},"expires":{"format":"uint64","minimum":0,"type":"integer"},"kind":{"const":"invitation","type":"string"},"link":{"type":"string"},"localOnly":{"default":false,"type":"boolean"}},"required":["kind","channel","link","expires"],"type":"object"},{"properties":{"kind":{"const":"text","type":"string"},"text":{"type":"string"},"title":{"type":"string"}},"required":["kind","title","text"],"type":"object"},{"properties":{"kind":{"const":"status","type":"string"},"text":{"type":"string"}},"required":["kind","text"],"type":"object"},{"properties":{"conversation":{"type":"string"},"kind":{"const":"close","type":"string"}},"required":["kind","conversation"],"type":"object"}]},"CommandSpec":{"properties":{"available":{"type":"boolean"},"capability":{"type":["string","null"]},"description":{"type":"string"},"name":{"type":"string"},"scope":{"type":"string"},"usage":{"type":"string"}},"required":["name","usage","description","scope","available"],"type":"object"},"Conversation":{"properties":{"active":{"type":"boolean"},"channelId":{"type":"string"},"commands":{"default":[],"items":{"$ref":"#/$defs/CommandSpec"},"type":"array"},"directory":{"default":null,"type":["string","null"]},"id":{"type":"string"},"inputLimitBytes":{"default":12000,"format":"uint","minimum":0,"type":"integer"},"kind":{"$ref":"#/$defs/ConversationKind"},"lastMessageId":{"type":["string","null"]},"members":{"items":{"$ref":"#/$defs/Member"},"type":"array"},"name":{"type":"string"},"owner":{"type":"boolean"},"provider":{"default":null,"type":["string","null"]},"topic":{"type":"string"},"unread":{"format":"uint32","minimum":0,"type":"integer"},"visibility":{"default":null,"type":["string","null"]}},"required":["id","channelId","kind","name","topic","active","owner","members","unread"],"type":"object"},"ConversationKind":{"enum":["channel","query","archive"],"type":"string"},"DirectoryEntry":{"properties":{"conversation":{"type":["string","null"]},"joined":{"type":"boolean"},"name":{"type":"string"}},"required":["name","joined"],"type":"object"},"InputHistoryEntry":{"properties":{"conversation":{"type":["string","null"]},"text":{"type":"string"}},"required":["text"],"type":"object"},"InstanceInfo":{"properties":{"archiveExists":{"type":"boolean"},"bootId":{"type":"string"},"capabilities":{"items":{"type":"string"},"type":"array"},"id":{"type":"string"},"label":{"type":"string"},"locked":{"type":"boolean"},"profileExists":{"type":"boolean"},"protocolLocked":{"type":"boolean"},"safetyNumber":{"type":"string"}},"required":["id","label","bootId","locked","protocolLocked","profileExists","archiveExists","safetyNumber","capabilities"],"type":"object"},"Member":{"properties":{"capabilities":{"default":[],"items":{"type":"string"},"type":"array"},"id":{"type":"string"},"isSelf":{"type":"boolean"},"nickname":{"type":"string"},"recentlyActive":{"default":null,"type":["boolean","null"]}},"required":["id","nickname","isSelf"],"type":"object"},"OperationDetail":{"description":"Safe metadata plus the protected result retained in the encrypted operation journal.","properties":{"action":{"type":"string"},"conversation":{"type":["string","null"]},"id":{"type":"string"},"instance":{"type":"string"},"message":{"type":["string","null"]},"network":{"default":null,"type":["string","null"]},"output":{"anyOf":[{"$ref":"#/$defs/CommandOutput"},{"type":"null"}]},"started":{"format":"uint64","minimum":0,"type":"integer"},"state":{"type":"string"}},"required":["id","instance","action","started","state"],"type":"object"},"ProviderStatus":{"properties":{"code":{"type":"string"},"id":{"type":"string"},"message":{"type":"string"},"retryable":{"type":"boolean"}},"required":["id","code","message","retryable"],"type":"object"}},"$schema":"https://json-schema.org/draft/2020-12/schema","properties":{"activity":{"default":null,"items":{"$ref":"#/$defs/Activity"},"type":["array","null"]},"commandHistory":{"items":{"type":"string"},"type":"array"},"conversations":{"items":{"$ref":"#/$defs/Conversation"},"type":"array"},"inputHistory":{"items":{"$ref":"#/$defs/InputHistoryEntry"},"type":"array"},"instance":{"$ref":"#/$defs/InstanceInfo"},"operations":{"default":null,"items":{"$ref":"#/$defs/OperationDetail"},"type":["array","null"]},"presenceEnabled":{"default":null,"type":["boolean","null"]},"providerErrors":{"default":[],"items":{"$ref":"#/$defs/ProviderStatus"},"type":"array"},"revision":{"type":"string"}},"required":["instance","revision","conversations","commandHistory","inputHistory"],"title":"Snapshot","type":"object"};
const schema145 = {"description":"Authenticated state changes observed by this profile, retained before publication.","properties":{"conversation":{"type":"string"},"id":{"type":"string"},"kind":{"type":"string"},"text":{"type":"string"},"timestamp":{"format":"uint64","minimum":0,"type":"integer"}},"required":["id","conversation","kind","text","timestamp"],"type":"object"};
const schema150 = {"properties":{"conversation":{"type":["string","null"]},"text":{"type":"string"}},"required":["text"],"type":"object"};
const schema151 = {"properties":{"archiveExists":{"type":"boolean"},"bootId":{"type":"string"},"capabilities":{"items":{"type":"string"},"type":"array"},"id":{"type":"string"},"label":{"type":"string"},"locked":{"type":"boolean"},"profileExists":{"type":"boolean"},"protocolLocked":{"type":"boolean"},"safetyNumber":{"type":"string"}},"required":["id","label","bootId","locked","protocolLocked","profileExists","archiveExists","safetyNumber","capabilities"],"type":"object"};
const schema156 = {"properties":{"code":{"type":"string"},"id":{"type":"string"},"message":{"type":"string"},"retryable":{"type":"boolean"}},"required":["id","code","message","retryable"],"type":"object"};
const schema146 = {"properties":{"active":{"type":"boolean"},"channelId":{"type":"string"},"commands":{"default":[],"items":{"$ref":"#/$defs/CommandSpec"},"type":"array"},"directory":{"default":null,"type":["string","null"]},"id":{"type":"string"},"inputLimitBytes":{"default":12000,"format":"uint","minimum":0,"type":"integer"},"kind":{"$ref":"#/$defs/ConversationKind"},"lastMessageId":{"type":["string","null"]},"members":{"items":{"$ref":"#/$defs/Member"},"type":"array"},"name":{"type":"string"},"owner":{"type":"boolean"},"provider":{"default":null,"type":["string","null"]},"topic":{"type":"string"},"unread":{"format":"uint32","minimum":0,"type":"integer"},"visibility":{"default":null,"type":["string","null"]}},"required":["id","channelId","kind","name","topic","active","owner","members","unread"],"type":"object"};
const schema147 = {"properties":{"available":{"type":"boolean"},"capability":{"type":["string","null"]},"description":{"type":"string"},"name":{"type":"string"},"scope":{"type":"string"},"usage":{"type":"string"}},"required":["name","usage","description","scope","available"],"type":"object"};
const schema148 = {"enum":["channel","query","archive"],"type":"string"};
const schema149 = {"properties":{"capabilities":{"default":[],"items":{"type":"string"},"type":"array"},"id":{"type":"string"},"isSelf":{"type":"boolean"},"nickname":{"type":"string"},"recentlyActive":{"default":null,"type":["boolean","null"]}},"required":["id","nickname","isSelf"],"type":"object"};

function validate125(data, {instancePath="", parentData, parentDataProperty, rootData=data, dynamicAnchors={}}={}){
let vErrors = null;
let errors = 0;
const evaluated0 = validate125.evaluated;
if(evaluated0.dynamicProps){
evaluated0.props = undefined;
}
if(evaluated0.dynamicItems){
evaluated0.items = undefined;
}
if(errors === 0){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing0;
if((((((((((data.id === undefined) && (missing0 = "id")) || ((data.channelId === undefined) && (missing0 = "channelId"))) || ((data.kind === undefined) && (missing0 = "kind"))) || ((data.name === undefined) && (missing0 = "name"))) || ((data.topic === undefined) && (missing0 = "topic"))) || ((data.active === undefined) && (missing0 = "active"))) || ((data.owner === undefined) && (missing0 = "owner"))) || ((data.members === undefined) && (missing0 = "members"))) || ((data.unread === undefined) && (missing0 = "unread"))){
validate125.errors = [{instancePath,schemaPath:"#/required",keyword:"required",params:{missingProperty: missing0},message:"must have required property '"+missing0+"'"}];
return false;
}
else {
if(data.active !== undefined){
const _errs1 = errors;
if(typeof data.active !== "boolean"){
validate125.errors = [{instancePath:instancePath+"/active",schemaPath:"#/properties/active/type",keyword:"type",params:{type: "boolean"},message:"must be boolean"}];
return false;
}
var valid0 = _errs1 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.channelId !== undefined){
const _errs3 = errors;
if(typeof data.channelId !== "string"){
validate125.errors = [{instancePath:instancePath+"/channelId",schemaPath:"#/properties/channelId/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs3 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.commands !== undefined){
let data2 = data.commands;
const _errs5 = errors;
if(errors === _errs5){
if(Array.isArray(data2)){
var valid1 = true;
const len0 = data2.length;
for(let i0=0; i0<len0; i0++){
let data3 = data2[i0];
const _errs7 = errors;
const _errs8 = errors;
if(errors === _errs8){
if(data3 && typeof data3 == "object" && !Array.isArray(data3)){
let missing1;
if((((((data3.name === undefined) && (missing1 = "name")) || ((data3.usage === undefined) && (missing1 = "usage"))) || ((data3.description === undefined) && (missing1 = "description"))) || ((data3.scope === undefined) && (missing1 = "scope"))) || ((data3.available === undefined) && (missing1 = "available"))){
validate125.errors = [{instancePath:instancePath+"/commands/" + i0,schemaPath:"#/$defs/CommandSpec/required",keyword:"required",params:{missingProperty: missing1},message:"must have required property '"+missing1+"'"}];
return false;
}
else {
if(data3.available !== undefined){
const _errs10 = errors;
if(typeof data3.available !== "boolean"){
validate125.errors = [{instancePath:instancePath+"/commands/" + i0+"/available",schemaPath:"#/$defs/CommandSpec/properties/available/type",keyword:"type",params:{type: "boolean"},message:"must be boolean"}];
return false;
}
var valid3 = _errs10 === errors;
}
else {
var valid3 = true;
}
if(valid3){
if(data3.capability !== undefined){
let data5 = data3.capability;
const _errs12 = errors;
if((typeof data5 !== "string") && (data5 !== null)){
validate125.errors = [{instancePath:instancePath+"/commands/" + i0+"/capability",schemaPath:"#/$defs/CommandSpec/properties/capability/type",keyword:"type",params:{type: schema147.properties.capability.type},message:"must be string,null"}];
return false;
}
var valid3 = _errs12 === errors;
}
else {
var valid3 = true;
}
if(valid3){
if(data3.description !== undefined){
const _errs14 = errors;
if(typeof data3.description !== "string"){
validate125.errors = [{instancePath:instancePath+"/commands/" + i0+"/description",schemaPath:"#/$defs/CommandSpec/properties/description/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid3 = _errs14 === errors;
}
else {
var valid3 = true;
}
if(valid3){
if(data3.name !== undefined){
const _errs16 = errors;
if(typeof data3.name !== "string"){
validate125.errors = [{instancePath:instancePath+"/commands/" + i0+"/name",schemaPath:"#/$defs/CommandSpec/properties/name/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid3 = _errs16 === errors;
}
else {
var valid3 = true;
}
if(valid3){
if(data3.scope !== undefined){
const _errs18 = errors;
if(typeof data3.scope !== "string"){
validate125.errors = [{instancePath:instancePath+"/commands/" + i0+"/scope",schemaPath:"#/$defs/CommandSpec/properties/scope/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid3 = _errs18 === errors;
}
else {
var valid3 = true;
}
if(valid3){
if(data3.usage !== undefined){
const _errs20 = errors;
if(typeof data3.usage !== "string"){
validate125.errors = [{instancePath:instancePath+"/commands/" + i0+"/usage",schemaPath:"#/$defs/CommandSpec/properties/usage/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid3 = _errs20 === errors;
}
else {
var valid3 = true;
}
}
}
}
}
}
}
}
else {
validate125.errors = [{instancePath:instancePath+"/commands/" + i0,schemaPath:"#/$defs/CommandSpec/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
var valid1 = _errs7 === errors;
if(!valid1){
break;
}
}
}
else {
validate125.errors = [{instancePath:instancePath+"/commands",schemaPath:"#/properties/commands/type",keyword:"type",params:{type: "array"},message:"must be array"}];
return false;
}
}
var valid0 = _errs5 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.directory !== undefined){
let data10 = data.directory;
const _errs22 = errors;
if((typeof data10 !== "string") && (data10 !== null)){
validate125.errors = [{instancePath:instancePath+"/directory",schemaPath:"#/properties/directory/type",keyword:"type",params:{type: schema146.properties.directory.type},message:"must be string,null"}];
return false;
}
var valid0 = _errs22 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.id !== undefined){
const _errs24 = errors;
if(typeof data.id !== "string"){
validate125.errors = [{instancePath:instancePath+"/id",schemaPath:"#/properties/id/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs24 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.inputLimitBytes !== undefined){
let data12 = data.inputLimitBytes;
const _errs26 = errors;
if(!(((typeof data12 == "number") && (!(data12 % 1) && !isNaN(data12))) && (isFinite(data12)))){
validate125.errors = [{instancePath:instancePath+"/inputLimitBytes",schemaPath:"#/properties/inputLimitBytes/type",keyword:"type",params:{type: "integer"},message:"must be integer"}];
return false;
}
if(errors === _errs26){
if((typeof data12 == "number") && (isFinite(data12))){
if(data12 < 0 || isNaN(data12)){
validate125.errors = [{instancePath:instancePath+"/inputLimitBytes",schemaPath:"#/properties/inputLimitBytes/minimum",keyword:"minimum",params:{comparison: ">=", limit: 0},message:"must be >= 0"}];
return false;
}
}
}
var valid0 = _errs26 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.kind !== undefined){
let data13 = data.kind;
const _errs28 = errors;
if(typeof data13 !== "string"){
validate125.errors = [{instancePath:instancePath+"/kind",schemaPath:"#/$defs/ConversationKind/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
if(!(((data13 === "channel") || (data13 === "query")) || (data13 === "archive"))){
validate125.errors = [{instancePath:instancePath+"/kind",schemaPath:"#/$defs/ConversationKind/enum",keyword:"enum",params:{allowedValues: schema148.enum},message:"must be equal to one of the allowed values"}];
return false;
}
var valid0 = _errs28 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.lastMessageId !== undefined){
let data14 = data.lastMessageId;
const _errs31 = errors;
if((typeof data14 !== "string") && (data14 !== null)){
validate125.errors = [{instancePath:instancePath+"/lastMessageId",schemaPath:"#/properties/lastMessageId/type",keyword:"type",params:{type: schema146.properties.lastMessageId.type},message:"must be string,null"}];
return false;
}
var valid0 = _errs31 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.members !== undefined){
let data15 = data.members;
const _errs33 = errors;
if(errors === _errs33){
if(Array.isArray(data15)){
var valid5 = true;
const len1 = data15.length;
for(let i1=0; i1<len1; i1++){
let data16 = data15[i1];
const _errs35 = errors;
const _errs36 = errors;
if(errors === _errs36){
if(data16 && typeof data16 == "object" && !Array.isArray(data16)){
let missing2;
if((((data16.id === undefined) && (missing2 = "id")) || ((data16.nickname === undefined) && (missing2 = "nickname"))) || ((data16.isSelf === undefined) && (missing2 = "isSelf"))){
validate125.errors = [{instancePath:instancePath+"/members/" + i1,schemaPath:"#/$defs/Member/required",keyword:"required",params:{missingProperty: missing2},message:"must have required property '"+missing2+"'"}];
return false;
}
else {
if(data16.capabilities !== undefined){
let data17 = data16.capabilities;
const _errs38 = errors;
if(errors === _errs38){
if(Array.isArray(data17)){
var valid8 = true;
const len2 = data17.length;
for(let i2=0; i2<len2; i2++){
const _errs40 = errors;
if(typeof data17[i2] !== "string"){
validate125.errors = [{instancePath:instancePath+"/members/" + i1+"/capabilities/" + i2,schemaPath:"#/$defs/Member/properties/capabilities/items/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid8 = _errs40 === errors;
if(!valid8){
break;
}
}
}
else {
validate125.errors = [{instancePath:instancePath+"/members/" + i1+"/capabilities",schemaPath:"#/$defs/Member/properties/capabilities/type",keyword:"type",params:{type: "array"},message:"must be array"}];
return false;
}
}
var valid7 = _errs38 === errors;
}
else {
var valid7 = true;
}
if(valid7){
if(data16.id !== undefined){
const _errs42 = errors;
if(typeof data16.id !== "string"){
validate125.errors = [{instancePath:instancePath+"/members/" + i1+"/id",schemaPath:"#/$defs/Member/properties/id/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid7 = _errs42 === errors;
}
else {
var valid7 = true;
}
if(valid7){
if(data16.isSelf !== undefined){
const _errs44 = errors;
if(typeof data16.isSelf !== "boolean"){
validate125.errors = [{instancePath:instancePath+"/members/" + i1+"/isSelf",schemaPath:"#/$defs/Member/properties/isSelf/type",keyword:"type",params:{type: "boolean"},message:"must be boolean"}];
return false;
}
var valid7 = _errs44 === errors;
}
else {
var valid7 = true;
}
if(valid7){
if(data16.nickname !== undefined){
const _errs46 = errors;
if(typeof data16.nickname !== "string"){
validate125.errors = [{instancePath:instancePath+"/members/" + i1+"/nickname",schemaPath:"#/$defs/Member/properties/nickname/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid7 = _errs46 === errors;
}
else {
var valid7 = true;
}
if(valid7){
if(data16.recentlyActive !== undefined){
let data22 = data16.recentlyActive;
const _errs48 = errors;
if((typeof data22 !== "boolean") && (data22 !== null)){
validate125.errors = [{instancePath:instancePath+"/members/" + i1+"/recentlyActive",schemaPath:"#/$defs/Member/properties/recentlyActive/type",keyword:"type",params:{type: schema149.properties.recentlyActive.type},message:"must be boolean,null"}];
return false;
}
var valid7 = _errs48 === errors;
}
else {
var valid7 = true;
}
}
}
}
}
}
}
else {
validate125.errors = [{instancePath:instancePath+"/members/" + i1,schemaPath:"#/$defs/Member/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
var valid5 = _errs35 === errors;
if(!valid5){
break;
}
}
}
else {
validate125.errors = [{instancePath:instancePath+"/members",schemaPath:"#/properties/members/type",keyword:"type",params:{type: "array"},message:"must be array"}];
return false;
}
}
var valid0 = _errs33 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.name !== undefined){
const _errs50 = errors;
if(typeof data.name !== "string"){
validate125.errors = [{instancePath:instancePath+"/name",schemaPath:"#/properties/name/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs50 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.owner !== undefined){
const _errs52 = errors;
if(typeof data.owner !== "boolean"){
validate125.errors = [{instancePath:instancePath+"/owner",schemaPath:"#/properties/owner/type",keyword:"type",params:{type: "boolean"},message:"must be boolean"}];
return false;
}
var valid0 = _errs52 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.provider !== undefined){
let data25 = data.provider;
const _errs54 = errors;
if((typeof data25 !== "string") && (data25 !== null)){
validate125.errors = [{instancePath:instancePath+"/provider",schemaPath:"#/properties/provider/type",keyword:"type",params:{type: schema146.properties.provider.type},message:"must be string,null"}];
return false;
}
var valid0 = _errs54 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.topic !== undefined){
const _errs56 = errors;
if(typeof data.topic !== "string"){
validate125.errors = [{instancePath:instancePath+"/topic",schemaPath:"#/properties/topic/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs56 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.unread !== undefined){
let data27 = data.unread;
const _errs58 = errors;
if(!(((typeof data27 == "number") && (!(data27 % 1) && !isNaN(data27))) && (isFinite(data27)))){
validate125.errors = [{instancePath:instancePath+"/unread",schemaPath:"#/properties/unread/type",keyword:"type",params:{type: "integer"},message:"must be integer"}];
return false;
}
if(errors === _errs58){
if((typeof data27 == "number") && (isFinite(data27))){
if(data27 < 0 || isNaN(data27)){
validate125.errors = [{instancePath:instancePath+"/unread",schemaPath:"#/properties/unread/minimum",keyword:"minimum",params:{comparison: ">=", limit: 0},message:"must be >= 0"}];
return false;
}
}
}
var valid0 = _errs58 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.visibility !== undefined){
let data28 = data.visibility;
const _errs60 = errors;
if((typeof data28 !== "string") && (data28 !== null)){
validate125.errors = [{instancePath:instancePath+"/visibility",schemaPath:"#/properties/visibility/type",keyword:"type",params:{type: schema146.properties.visibility.type},message:"must be string,null"}];
return false;
}
var valid0 = _errs60 === errors;
}
else {
var valid0 = true;
}
}
}
}
}
}
}
}
}
}
}
}
}
}
}
}
}
else {
validate125.errors = [{instancePath,schemaPath:"#/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
validate125.errors = vErrors;
return errors === 0;
}
validate125.evaluated = {"props":{"active":true,"channelId":true,"commands":true,"directory":true,"id":true,"inputLimitBytes":true,"kind":true,"lastMessageId":true,"members":true,"name":true,"owner":true,"provider":true,"topic":true,"unread":true,"visibility":true},"dynamicProps":false,"dynamicItems":false};

const schema152 = {"description":"Safe metadata plus the protected result retained in the encrypted operation journal.","properties":{"action":{"type":"string"},"conversation":{"type":["string","null"]},"id":{"type":"string"},"instance":{"type":"string"},"message":{"type":["string","null"]},"network":{"default":null,"type":["string","null"]},"output":{"anyOf":[{"$ref":"#/$defs/CommandOutput"},{"type":"null"}]},"started":{"format":"uint64","minimum":0,"type":"integer"},"state":{"type":"string"}},"required":["id","instance","action","started","state"],"type":"object"};
const schema153 = {"oneOf":[{"properties":{"commands":{"items":{"$ref":"#/$defs/CommandSpec"},"type":"array"},"kind":{"const":"help","type":"string"}},"required":["kind","commands"],"type":"object"},{"properties":{"channels":{"items":{"$ref":"#/$defs/DirectoryEntry"},"type":"array"},"kind":{"const":"directory","type":"string"}},"required":["kind","channels"],"type":"object"},{"properties":{"channel":{"type":"string"},"expires":{"format":"uint64","minimum":0,"type":"integer"},"kind":{"const":"invitation","type":"string"},"link":{"type":"string"},"localOnly":{"default":false,"type":"boolean"}},"required":["kind","channel","link","expires"],"type":"object"},{"properties":{"kind":{"const":"text","type":"string"},"text":{"type":"string"},"title":{"type":"string"}},"required":["kind","title","text"],"type":"object"},{"properties":{"kind":{"const":"status","type":"string"},"text":{"type":"string"}},"required":["kind","text"],"type":"object"},{"properties":{"conversation":{"type":"string"},"kind":{"const":"close","type":"string"}},"required":["kind","conversation"],"type":"object"}]};
const schema155 = {"properties":{"conversation":{"type":["string","null"]},"joined":{"type":"boolean"},"name":{"type":"string"}},"required":["name","joined"],"type":"object"};

function validate128(data, {instancePath="", parentData, parentDataProperty, rootData=data, dynamicAnchors={}}={}){
let vErrors = null;
let errors = 0;
const evaluated0 = validate128.evaluated;
if(evaluated0.dynamicProps){
evaluated0.props = undefined;
}
if(evaluated0.dynamicItems){
evaluated0.items = undefined;
}
const _errs0 = errors;
let valid0 = false;
let passing0 = null;
const _errs1 = errors;
if(errors === _errs1){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing0;
if(((data.kind === undefined) && (missing0 = "kind")) || ((data.commands === undefined) && (missing0 = "commands"))){
const err0 = {instancePath,schemaPath:"#/oneOf/0/required",keyword:"required",params:{missingProperty: missing0},message:"must have required property '"+missing0+"'"};
if(vErrors === null){
vErrors = [err0];
}
else {
vErrors.push(err0);
}
errors++;
}
else {
if(data.commands !== undefined){
let data0 = data.commands;
const _errs3 = errors;
if(errors === _errs3){
if(Array.isArray(data0)){
var valid2 = true;
const len0 = data0.length;
for(let i0=0; i0<len0; i0++){
let data1 = data0[i0];
const _errs5 = errors;
const _errs6 = errors;
if(errors === _errs6){
if(data1 && typeof data1 == "object" && !Array.isArray(data1)){
let missing1;
if((((((data1.name === undefined) && (missing1 = "name")) || ((data1.usage === undefined) && (missing1 = "usage"))) || ((data1.description === undefined) && (missing1 = "description"))) || ((data1.scope === undefined) && (missing1 = "scope"))) || ((data1.available === undefined) && (missing1 = "available"))){
const err1 = {instancePath:instancePath+"/commands/" + i0,schemaPath:"#/$defs/CommandSpec/required",keyword:"required",params:{missingProperty: missing1},message:"must have required property '"+missing1+"'"};
if(vErrors === null){
vErrors = [err1];
}
else {
vErrors.push(err1);
}
errors++;
}
else {
if(data1.available !== undefined){
const _errs8 = errors;
if(typeof data1.available !== "boolean"){
const err2 = {instancePath:instancePath+"/commands/" + i0+"/available",schemaPath:"#/$defs/CommandSpec/properties/available/type",keyword:"type",params:{type: "boolean"},message:"must be boolean"};
if(vErrors === null){
vErrors = [err2];
}
else {
vErrors.push(err2);
}
errors++;
}
var valid4 = _errs8 === errors;
}
else {
var valid4 = true;
}
if(valid4){
if(data1.capability !== undefined){
let data3 = data1.capability;
const _errs10 = errors;
if((typeof data3 !== "string") && (data3 !== null)){
const err3 = {instancePath:instancePath+"/commands/" + i0+"/capability",schemaPath:"#/$defs/CommandSpec/properties/capability/type",keyword:"type",params:{type: schema147.properties.capability.type},message:"must be string,null"};
if(vErrors === null){
vErrors = [err3];
}
else {
vErrors.push(err3);
}
errors++;
}
var valid4 = _errs10 === errors;
}
else {
var valid4 = true;
}
if(valid4){
if(data1.description !== undefined){
const _errs12 = errors;
if(typeof data1.description !== "string"){
const err4 = {instancePath:instancePath+"/commands/" + i0+"/description",schemaPath:"#/$defs/CommandSpec/properties/description/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err4];
}
else {
vErrors.push(err4);
}
errors++;
}
var valid4 = _errs12 === errors;
}
else {
var valid4 = true;
}
if(valid4){
if(data1.name !== undefined){
const _errs14 = errors;
if(typeof data1.name !== "string"){
const err5 = {instancePath:instancePath+"/commands/" + i0+"/name",schemaPath:"#/$defs/CommandSpec/properties/name/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err5];
}
else {
vErrors.push(err5);
}
errors++;
}
var valid4 = _errs14 === errors;
}
else {
var valid4 = true;
}
if(valid4){
if(data1.scope !== undefined){
const _errs16 = errors;
if(typeof data1.scope !== "string"){
const err6 = {instancePath:instancePath+"/commands/" + i0+"/scope",schemaPath:"#/$defs/CommandSpec/properties/scope/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err6];
}
else {
vErrors.push(err6);
}
errors++;
}
var valid4 = _errs16 === errors;
}
else {
var valid4 = true;
}
if(valid4){
if(data1.usage !== undefined){
const _errs18 = errors;
if(typeof data1.usage !== "string"){
const err7 = {instancePath:instancePath+"/commands/" + i0+"/usage",schemaPath:"#/$defs/CommandSpec/properties/usage/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err7];
}
else {
vErrors.push(err7);
}
errors++;
}
var valid4 = _errs18 === errors;
}
else {
var valid4 = true;
}
}
}
}
}
}
}
}
else {
const err8 = {instancePath:instancePath+"/commands/" + i0,schemaPath:"#/$defs/CommandSpec/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err8];
}
else {
vErrors.push(err8);
}
errors++;
}
}
var valid2 = _errs5 === errors;
if(!valid2){
break;
}
}
}
else {
const err9 = {instancePath:instancePath+"/commands",schemaPath:"#/oneOf/0/properties/commands/type",keyword:"type",params:{type: "array"},message:"must be array"};
if(vErrors === null){
vErrors = [err9];
}
else {
vErrors.push(err9);
}
errors++;
}
}
var valid1 = _errs3 === errors;
}
else {
var valid1 = true;
}
if(valid1){
if(data.kind !== undefined){
let data8 = data.kind;
const _errs20 = errors;
if(typeof data8 !== "string"){
const err10 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/0/properties/kind/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err10];
}
else {
vErrors.push(err10);
}
errors++;
}
if("help" !== data8){
const err11 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/0/properties/kind/const",keyword:"const",params:{allowedValue: "help"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err11];
}
else {
vErrors.push(err11);
}
errors++;
}
var valid1 = _errs20 === errors;
}
else {
var valid1 = true;
}
}
}
}
else {
const err12 = {instancePath,schemaPath:"#/oneOf/0/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err12];
}
else {
vErrors.push(err12);
}
errors++;
}
}
var _valid0 = _errs1 === errors;
if(_valid0){
valid0 = true;
passing0 = 0;
var props0 = {};
props0.commands = true;
props0.kind = true;
}
const _errs22 = errors;
if(errors === _errs22){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing2;
if(((data.kind === undefined) && (missing2 = "kind")) || ((data.channels === undefined) && (missing2 = "channels"))){
const err13 = {instancePath,schemaPath:"#/oneOf/1/required",keyword:"required",params:{missingProperty: missing2},message:"must have required property '"+missing2+"'"};
if(vErrors === null){
vErrors = [err13];
}
else {
vErrors.push(err13);
}
errors++;
}
else {
if(data.channels !== undefined){
let data9 = data.channels;
const _errs24 = errors;
if(errors === _errs24){
if(Array.isArray(data9)){
var valid6 = true;
const len1 = data9.length;
for(let i1=0; i1<len1; i1++){
let data10 = data9[i1];
const _errs26 = errors;
const _errs27 = errors;
if(errors === _errs27){
if(data10 && typeof data10 == "object" && !Array.isArray(data10)){
let missing3;
if(((data10.name === undefined) && (missing3 = "name")) || ((data10.joined === undefined) && (missing3 = "joined"))){
const err14 = {instancePath:instancePath+"/channels/" + i1,schemaPath:"#/$defs/DirectoryEntry/required",keyword:"required",params:{missingProperty: missing3},message:"must have required property '"+missing3+"'"};
if(vErrors === null){
vErrors = [err14];
}
else {
vErrors.push(err14);
}
errors++;
}
else {
if(data10.conversation !== undefined){
let data11 = data10.conversation;
const _errs29 = errors;
if((typeof data11 !== "string") && (data11 !== null)){
const err15 = {instancePath:instancePath+"/channels/" + i1+"/conversation",schemaPath:"#/$defs/DirectoryEntry/properties/conversation/type",keyword:"type",params:{type: schema155.properties.conversation.type},message:"must be string,null"};
if(vErrors === null){
vErrors = [err15];
}
else {
vErrors.push(err15);
}
errors++;
}
var valid8 = _errs29 === errors;
}
else {
var valid8 = true;
}
if(valid8){
if(data10.joined !== undefined){
const _errs31 = errors;
if(typeof data10.joined !== "boolean"){
const err16 = {instancePath:instancePath+"/channels/" + i1+"/joined",schemaPath:"#/$defs/DirectoryEntry/properties/joined/type",keyword:"type",params:{type: "boolean"},message:"must be boolean"};
if(vErrors === null){
vErrors = [err16];
}
else {
vErrors.push(err16);
}
errors++;
}
var valid8 = _errs31 === errors;
}
else {
var valid8 = true;
}
if(valid8){
if(data10.name !== undefined){
const _errs33 = errors;
if(typeof data10.name !== "string"){
const err17 = {instancePath:instancePath+"/channels/" + i1+"/name",schemaPath:"#/$defs/DirectoryEntry/properties/name/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err17];
}
else {
vErrors.push(err17);
}
errors++;
}
var valid8 = _errs33 === errors;
}
else {
var valid8 = true;
}
}
}
}
}
else {
const err18 = {instancePath:instancePath+"/channels/" + i1,schemaPath:"#/$defs/DirectoryEntry/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err18];
}
else {
vErrors.push(err18);
}
errors++;
}
}
var valid6 = _errs26 === errors;
if(!valid6){
break;
}
}
}
else {
const err19 = {instancePath:instancePath+"/channels",schemaPath:"#/oneOf/1/properties/channels/type",keyword:"type",params:{type: "array"},message:"must be array"};
if(vErrors === null){
vErrors = [err19];
}
else {
vErrors.push(err19);
}
errors++;
}
}
var valid5 = _errs24 === errors;
}
else {
var valid5 = true;
}
if(valid5){
if(data.kind !== undefined){
let data14 = data.kind;
const _errs35 = errors;
if(typeof data14 !== "string"){
const err20 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/1/properties/kind/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err20];
}
else {
vErrors.push(err20);
}
errors++;
}
if("directory" !== data14){
const err21 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/1/properties/kind/const",keyword:"const",params:{allowedValue: "directory"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err21];
}
else {
vErrors.push(err21);
}
errors++;
}
var valid5 = _errs35 === errors;
}
else {
var valid5 = true;
}
}
}
}
else {
const err22 = {instancePath,schemaPath:"#/oneOf/1/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err22];
}
else {
vErrors.push(err22);
}
errors++;
}
}
var _valid0 = _errs22 === errors;
if(_valid0 && valid0){
valid0 = false;
passing0 = [passing0, 1];
}
else {
if(_valid0){
valid0 = true;
passing0 = 1;
if(props0 !== true){
props0 = props0 || {};
props0.channels = true;
props0.kind = true;
}
}
const _errs37 = errors;
if(errors === _errs37){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing4;
if(((((data.kind === undefined) && (missing4 = "kind")) || ((data.channel === undefined) && (missing4 = "channel"))) || ((data.link === undefined) && (missing4 = "link"))) || ((data.expires === undefined) && (missing4 = "expires"))){
const err23 = {instancePath,schemaPath:"#/oneOf/2/required",keyword:"required",params:{missingProperty: missing4},message:"must have required property '"+missing4+"'"};
if(vErrors === null){
vErrors = [err23];
}
else {
vErrors.push(err23);
}
errors++;
}
else {
if(data.channel !== undefined){
const _errs39 = errors;
if(typeof data.channel !== "string"){
const err24 = {instancePath:instancePath+"/channel",schemaPath:"#/oneOf/2/properties/channel/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err24];
}
else {
vErrors.push(err24);
}
errors++;
}
var valid9 = _errs39 === errors;
}
else {
var valid9 = true;
}
if(valid9){
if(data.expires !== undefined){
let data16 = data.expires;
const _errs41 = errors;
if(!(((typeof data16 == "number") && (!(data16 % 1) && !isNaN(data16))) && (isFinite(data16)))){
const err25 = {instancePath:instancePath+"/expires",schemaPath:"#/oneOf/2/properties/expires/type",keyword:"type",params:{type: "integer"},message:"must be integer"};
if(vErrors === null){
vErrors = [err25];
}
else {
vErrors.push(err25);
}
errors++;
}
if(errors === _errs41){
if((typeof data16 == "number") && (isFinite(data16))){
if(data16 < 0 || isNaN(data16)){
const err26 = {instancePath:instancePath+"/expires",schemaPath:"#/oneOf/2/properties/expires/minimum",keyword:"minimum",params:{comparison: ">=", limit: 0},message:"must be >= 0"};
if(vErrors === null){
vErrors = [err26];
}
else {
vErrors.push(err26);
}
errors++;
}
}
}
var valid9 = _errs41 === errors;
}
else {
var valid9 = true;
}
if(valid9){
if(data.kind !== undefined){
let data17 = data.kind;
const _errs43 = errors;
if(typeof data17 !== "string"){
const err27 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/2/properties/kind/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err27];
}
else {
vErrors.push(err27);
}
errors++;
}
if("invitation" !== data17){
const err28 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/2/properties/kind/const",keyword:"const",params:{allowedValue: "invitation"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err28];
}
else {
vErrors.push(err28);
}
errors++;
}
var valid9 = _errs43 === errors;
}
else {
var valid9 = true;
}
if(valid9){
if(data.link !== undefined){
const _errs45 = errors;
if(typeof data.link !== "string"){
const err29 = {instancePath:instancePath+"/link",schemaPath:"#/oneOf/2/properties/link/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err29];
}
else {
vErrors.push(err29);
}
errors++;
}
var valid9 = _errs45 === errors;
}
else {
var valid9 = true;
}
if(valid9){
if(data.localOnly !== undefined){
const _errs47 = errors;
if(typeof data.localOnly !== "boolean"){
const err30 = {instancePath:instancePath+"/localOnly",schemaPath:"#/oneOf/2/properties/localOnly/type",keyword:"type",params:{type: "boolean"},message:"must be boolean"};
if(vErrors === null){
vErrors = [err30];
}
else {
vErrors.push(err30);
}
errors++;
}
var valid9 = _errs47 === errors;
}
else {
var valid9 = true;
}
}
}
}
}
}
}
else {
const err31 = {instancePath,schemaPath:"#/oneOf/2/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err31];
}
else {
vErrors.push(err31);
}
errors++;
}
}
var _valid0 = _errs37 === errors;
if(_valid0 && valid0){
valid0 = false;
passing0 = [passing0, 2];
}
else {
if(_valid0){
valid0 = true;
passing0 = 2;
if(props0 !== true){
props0 = props0 || {};
props0.channel = true;
props0.expires = true;
props0.kind = true;
props0.link = true;
props0.localOnly = true;
}
}
const _errs49 = errors;
if(errors === _errs49){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing5;
if((((data.kind === undefined) && (missing5 = "kind")) || ((data.title === undefined) && (missing5 = "title"))) || ((data.text === undefined) && (missing5 = "text"))){
const err32 = {instancePath,schemaPath:"#/oneOf/3/required",keyword:"required",params:{missingProperty: missing5},message:"must have required property '"+missing5+"'"};
if(vErrors === null){
vErrors = [err32];
}
else {
vErrors.push(err32);
}
errors++;
}
else {
if(data.kind !== undefined){
let data20 = data.kind;
const _errs51 = errors;
if(typeof data20 !== "string"){
const err33 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/3/properties/kind/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err33];
}
else {
vErrors.push(err33);
}
errors++;
}
if("text" !== data20){
const err34 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/3/properties/kind/const",keyword:"const",params:{allowedValue: "text"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err34];
}
else {
vErrors.push(err34);
}
errors++;
}
var valid10 = _errs51 === errors;
}
else {
var valid10 = true;
}
if(valid10){
if(data.text !== undefined){
const _errs53 = errors;
if(typeof data.text !== "string"){
const err35 = {instancePath:instancePath+"/text",schemaPath:"#/oneOf/3/properties/text/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err35];
}
else {
vErrors.push(err35);
}
errors++;
}
var valid10 = _errs53 === errors;
}
else {
var valid10 = true;
}
if(valid10){
if(data.title !== undefined){
const _errs55 = errors;
if(typeof data.title !== "string"){
const err36 = {instancePath:instancePath+"/title",schemaPath:"#/oneOf/3/properties/title/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err36];
}
else {
vErrors.push(err36);
}
errors++;
}
var valid10 = _errs55 === errors;
}
else {
var valid10 = true;
}
}
}
}
}
else {
const err37 = {instancePath,schemaPath:"#/oneOf/3/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err37];
}
else {
vErrors.push(err37);
}
errors++;
}
}
var _valid0 = _errs49 === errors;
if(_valid0 && valid0){
valid0 = false;
passing0 = [passing0, 3];
}
else {
if(_valid0){
valid0 = true;
passing0 = 3;
if(props0 !== true){
props0 = props0 || {};
props0.kind = true;
props0.text = true;
props0.title = true;
}
}
const _errs57 = errors;
if(errors === _errs57){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing6;
if(((data.kind === undefined) && (missing6 = "kind")) || ((data.text === undefined) && (missing6 = "text"))){
const err38 = {instancePath,schemaPath:"#/oneOf/4/required",keyword:"required",params:{missingProperty: missing6},message:"must have required property '"+missing6+"'"};
if(vErrors === null){
vErrors = [err38];
}
else {
vErrors.push(err38);
}
errors++;
}
else {
if(data.kind !== undefined){
let data23 = data.kind;
const _errs59 = errors;
if(typeof data23 !== "string"){
const err39 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/4/properties/kind/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err39];
}
else {
vErrors.push(err39);
}
errors++;
}
if("status" !== data23){
const err40 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/4/properties/kind/const",keyword:"const",params:{allowedValue: "status"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err40];
}
else {
vErrors.push(err40);
}
errors++;
}
var valid11 = _errs59 === errors;
}
else {
var valid11 = true;
}
if(valid11){
if(data.text !== undefined){
const _errs61 = errors;
if(typeof data.text !== "string"){
const err41 = {instancePath:instancePath+"/text",schemaPath:"#/oneOf/4/properties/text/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err41];
}
else {
vErrors.push(err41);
}
errors++;
}
var valid11 = _errs61 === errors;
}
else {
var valid11 = true;
}
}
}
}
else {
const err42 = {instancePath,schemaPath:"#/oneOf/4/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err42];
}
else {
vErrors.push(err42);
}
errors++;
}
}
var _valid0 = _errs57 === errors;
if(_valid0 && valid0){
valid0 = false;
passing0 = [passing0, 4];
}
else {
if(_valid0){
valid0 = true;
passing0 = 4;
if(props0 !== true){
props0 = props0 || {};
props0.kind = true;
props0.text = true;
}
}
const _errs63 = errors;
if(errors === _errs63){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing7;
if(((data.kind === undefined) && (missing7 = "kind")) || ((data.conversation === undefined) && (missing7 = "conversation"))){
const err43 = {instancePath,schemaPath:"#/oneOf/5/required",keyword:"required",params:{missingProperty: missing7},message:"must have required property '"+missing7+"'"};
if(vErrors === null){
vErrors = [err43];
}
else {
vErrors.push(err43);
}
errors++;
}
else {
if(data.conversation !== undefined){
const _errs65 = errors;
if(typeof data.conversation !== "string"){
const err44 = {instancePath:instancePath+"/conversation",schemaPath:"#/oneOf/5/properties/conversation/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err44];
}
else {
vErrors.push(err44);
}
errors++;
}
var valid12 = _errs65 === errors;
}
else {
var valid12 = true;
}
if(valid12){
if(data.kind !== undefined){
let data26 = data.kind;
const _errs67 = errors;
if(typeof data26 !== "string"){
const err45 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/5/properties/kind/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err45];
}
else {
vErrors.push(err45);
}
errors++;
}
if("close" !== data26){
const err46 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/5/properties/kind/const",keyword:"const",params:{allowedValue: "close"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err46];
}
else {
vErrors.push(err46);
}
errors++;
}
var valid12 = _errs67 === errors;
}
else {
var valid12 = true;
}
}
}
}
else {
const err47 = {instancePath,schemaPath:"#/oneOf/5/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err47];
}
else {
vErrors.push(err47);
}
errors++;
}
}
var _valid0 = _errs63 === errors;
if(_valid0 && valid0){
valid0 = false;
passing0 = [passing0, 5];
}
else {
if(_valid0){
valid0 = true;
passing0 = 5;
if(props0 !== true){
props0 = props0 || {};
props0.conversation = true;
props0.kind = true;
}
}
}
}
}
}
}
if(!valid0){
const err48 = {instancePath,schemaPath:"#/oneOf",keyword:"oneOf",params:{passingSchemas: passing0},message:"must match exactly one schema in oneOf"};
if(vErrors === null){
vErrors = [err48];
}
else {
vErrors.push(err48);
}
errors++;
validate128.errors = vErrors;
return false;
}
else {
errors = _errs0;
if(vErrors !== null){
if(_errs0){
vErrors.length = _errs0;
}
else {
vErrors = null;
}
}
}
validate128.errors = vErrors;
evaluated0.props = props0;
return errors === 0;
}
validate128.evaluated = {"dynamicProps":true,"dynamicItems":false};


function validate127(data, {instancePath="", parentData, parentDataProperty, rootData=data, dynamicAnchors={}}={}){
let vErrors = null;
let errors = 0;
const evaluated0 = validate127.evaluated;
if(evaluated0.dynamicProps){
evaluated0.props = undefined;
}
if(evaluated0.dynamicItems){
evaluated0.items = undefined;
}
if(errors === 0){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing0;
if((((((data.id === undefined) && (missing0 = "id")) || ((data.instance === undefined) && (missing0 = "instance"))) || ((data.action === undefined) && (missing0 = "action"))) || ((data.started === undefined) && (missing0 = "started"))) || ((data.state === undefined) && (missing0 = "state"))){
validate127.errors = [{instancePath,schemaPath:"#/required",keyword:"required",params:{missingProperty: missing0},message:"must have required property '"+missing0+"'"}];
return false;
}
else {
if(data.action !== undefined){
const _errs1 = errors;
if(typeof data.action !== "string"){
validate127.errors = [{instancePath:instancePath+"/action",schemaPath:"#/properties/action/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs1 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.conversation !== undefined){
let data1 = data.conversation;
const _errs3 = errors;
if((typeof data1 !== "string") && (data1 !== null)){
validate127.errors = [{instancePath:instancePath+"/conversation",schemaPath:"#/properties/conversation/type",keyword:"type",params:{type: schema152.properties.conversation.type},message:"must be string,null"}];
return false;
}
var valid0 = _errs3 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.id !== undefined){
const _errs5 = errors;
if(typeof data.id !== "string"){
validate127.errors = [{instancePath:instancePath+"/id",schemaPath:"#/properties/id/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs5 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.instance !== undefined){
const _errs7 = errors;
if(typeof data.instance !== "string"){
validate127.errors = [{instancePath:instancePath+"/instance",schemaPath:"#/properties/instance/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs7 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.message !== undefined){
let data4 = data.message;
const _errs9 = errors;
if((typeof data4 !== "string") && (data4 !== null)){
validate127.errors = [{instancePath:instancePath+"/message",schemaPath:"#/properties/message/type",keyword:"type",params:{type: schema152.properties.message.type},message:"must be string,null"}];
return false;
}
var valid0 = _errs9 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.network !== undefined){
let data5 = data.network;
const _errs11 = errors;
if((typeof data5 !== "string") && (data5 !== null)){
validate127.errors = [{instancePath:instancePath+"/network",schemaPath:"#/properties/network/type",keyword:"type",params:{type: schema152.properties.network.type},message:"must be string,null"}];
return false;
}
var valid0 = _errs11 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.output !== undefined){
let data6 = data.output;
const _errs13 = errors;
const _errs14 = errors;
let valid1 = false;
const _errs15 = errors;
if(!(validate128(data6, {instancePath:instancePath+"/output",parentData:data,parentDataProperty:"output",rootData,dynamicAnchors}))){
vErrors = vErrors === null ? validate128.errors : vErrors.concat(validate128.errors);
errors = vErrors.length;
}
var _valid0 = _errs15 === errors;
valid1 = valid1 || _valid0;
const _errs16 = errors;
if(data6 !== null){
const err0 = {instancePath:instancePath+"/output",schemaPath:"#/properties/output/anyOf/1/type",keyword:"type",params:{type: "null"},message:"must be null"};
if(vErrors === null){
vErrors = [err0];
}
else {
vErrors.push(err0);
}
errors++;
}
var _valid0 = _errs16 === errors;
valid1 = valid1 || _valid0;
if(!valid1){
const err1 = {instancePath:instancePath+"/output",schemaPath:"#/properties/output/anyOf",keyword:"anyOf",params:{},message:"must match a schema in anyOf"};
if(vErrors === null){
vErrors = [err1];
}
else {
vErrors.push(err1);
}
errors++;
validate127.errors = vErrors;
return false;
}
else {
errors = _errs14;
if(vErrors !== null){
if(_errs14){
vErrors.length = _errs14;
}
else {
vErrors = null;
}
}
}
var valid0 = _errs13 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.started !== undefined){
let data7 = data.started;
const _errs18 = errors;
if(!(((typeof data7 == "number") && (!(data7 % 1) && !isNaN(data7))) && (isFinite(data7)))){
validate127.errors = [{instancePath:instancePath+"/started",schemaPath:"#/properties/started/type",keyword:"type",params:{type: "integer"},message:"must be integer"}];
return false;
}
if(errors === _errs18){
if((typeof data7 == "number") && (isFinite(data7))){
if(data7 < 0 || isNaN(data7)){
validate127.errors = [{instancePath:instancePath+"/started",schemaPath:"#/properties/started/minimum",keyword:"minimum",params:{comparison: ">=", limit: 0},message:"must be >= 0"}];
return false;
}
}
}
var valid0 = _errs18 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.state !== undefined){
const _errs20 = errors;
if(typeof data.state !== "string"){
validate127.errors = [{instancePath:instancePath+"/state",schemaPath:"#/properties/state/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs20 === errors;
}
else {
var valid0 = true;
}
}
}
}
}
}
}
}
}
}
}
else {
validate127.errors = [{instancePath,schemaPath:"#/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
validate127.errors = vErrors;
return errors === 0;
}
validate127.evaluated = {"props":{"action":true,"conversation":true,"id":true,"instance":true,"message":true,"network":true,"output":true,"started":true,"state":true},"dynamicProps":false,"dynamicItems":false};


function validate124(data, {instancePath="", parentData, parentDataProperty, rootData=data, dynamicAnchors={}}={}){
let vErrors = null;
let errors = 0;
const evaluated0 = validate124.evaluated;
if(evaluated0.dynamicProps){
evaluated0.props = undefined;
}
if(evaluated0.dynamicItems){
evaluated0.items = undefined;
}
if(errors === 0){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing0;
if((((((data.instance === undefined) && (missing0 = "instance")) || ((data.revision === undefined) && (missing0 = "revision"))) || ((data.conversations === undefined) && (missing0 = "conversations"))) || ((data.commandHistory === undefined) && (missing0 = "commandHistory"))) || ((data.inputHistory === undefined) && (missing0 = "inputHistory"))){
validate124.errors = [{instancePath,schemaPath:"#/required",keyword:"required",params:{missingProperty: missing0},message:"must have required property '"+missing0+"'"}];
return false;
}
else {
if(data.activity !== undefined){
let data0 = data.activity;
const _errs1 = errors;
if((!(Array.isArray(data0))) && (data0 !== null)){
validate124.errors = [{instancePath:instancePath+"/activity",schemaPath:"#/properties/activity/type",keyword:"type",params:{type: schema144.properties.activity.type},message:"must be array,null"}];
return false;
}
if(errors === _errs1){
if(Array.isArray(data0)){
var valid1 = true;
const len0 = data0.length;
for(let i0=0; i0<len0; i0++){
let data1 = data0[i0];
const _errs3 = errors;
const _errs4 = errors;
if(errors === _errs4){
if(data1 && typeof data1 == "object" && !Array.isArray(data1)){
let missing1;
if((((((data1.id === undefined) && (missing1 = "id")) || ((data1.conversation === undefined) && (missing1 = "conversation"))) || ((data1.kind === undefined) && (missing1 = "kind"))) || ((data1.text === undefined) && (missing1 = "text"))) || ((data1.timestamp === undefined) && (missing1 = "timestamp"))){
validate124.errors = [{instancePath:instancePath+"/activity/" + i0,schemaPath:"#/$defs/Activity/required",keyword:"required",params:{missingProperty: missing1},message:"must have required property '"+missing1+"'"}];
return false;
}
else {
if(data1.conversation !== undefined){
const _errs6 = errors;
if(typeof data1.conversation !== "string"){
validate124.errors = [{instancePath:instancePath+"/activity/" + i0+"/conversation",schemaPath:"#/$defs/Activity/properties/conversation/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid3 = _errs6 === errors;
}
else {
var valid3 = true;
}
if(valid3){
if(data1.id !== undefined){
const _errs8 = errors;
if(typeof data1.id !== "string"){
validate124.errors = [{instancePath:instancePath+"/activity/" + i0+"/id",schemaPath:"#/$defs/Activity/properties/id/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid3 = _errs8 === errors;
}
else {
var valid3 = true;
}
if(valid3){
if(data1.kind !== undefined){
const _errs10 = errors;
if(typeof data1.kind !== "string"){
validate124.errors = [{instancePath:instancePath+"/activity/" + i0+"/kind",schemaPath:"#/$defs/Activity/properties/kind/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid3 = _errs10 === errors;
}
else {
var valid3 = true;
}
if(valid3){
if(data1.text !== undefined){
const _errs12 = errors;
if(typeof data1.text !== "string"){
validate124.errors = [{instancePath:instancePath+"/activity/" + i0+"/text",schemaPath:"#/$defs/Activity/properties/text/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid3 = _errs12 === errors;
}
else {
var valid3 = true;
}
if(valid3){
if(data1.timestamp !== undefined){
let data6 = data1.timestamp;
const _errs14 = errors;
if(!(((typeof data6 == "number") && (!(data6 % 1) && !isNaN(data6))) && (isFinite(data6)))){
validate124.errors = [{instancePath:instancePath+"/activity/" + i0+"/timestamp",schemaPath:"#/$defs/Activity/properties/timestamp/type",keyword:"type",params:{type: "integer"},message:"must be integer"}];
return false;
}
if(errors === _errs14){
if((typeof data6 == "number") && (isFinite(data6))){
if(data6 < 0 || isNaN(data6)){
validate124.errors = [{instancePath:instancePath+"/activity/" + i0+"/timestamp",schemaPath:"#/$defs/Activity/properties/timestamp/minimum",keyword:"minimum",params:{comparison: ">=", limit: 0},message:"must be >= 0"}];
return false;
}
}
}
var valid3 = _errs14 === errors;
}
else {
var valid3 = true;
}
}
}
}
}
}
}
else {
validate124.errors = [{instancePath:instancePath+"/activity/" + i0,schemaPath:"#/$defs/Activity/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
var valid1 = _errs3 === errors;
if(!valid1){
break;
}
}
}
}
var valid0 = _errs1 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.commandHistory !== undefined){
let data7 = data.commandHistory;
const _errs16 = errors;
if(errors === _errs16){
if(Array.isArray(data7)){
var valid4 = true;
const len1 = data7.length;
for(let i1=0; i1<len1; i1++){
const _errs18 = errors;
if(typeof data7[i1] !== "string"){
validate124.errors = [{instancePath:instancePath+"/commandHistory/" + i1,schemaPath:"#/properties/commandHistory/items/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid4 = _errs18 === errors;
if(!valid4){
break;
}
}
}
else {
validate124.errors = [{instancePath:instancePath+"/commandHistory",schemaPath:"#/properties/commandHistory/type",keyword:"type",params:{type: "array"},message:"must be array"}];
return false;
}
}
var valid0 = _errs16 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.conversations !== undefined){
let data9 = data.conversations;
const _errs20 = errors;
if(errors === _errs20){
if(Array.isArray(data9)){
var valid5 = true;
const len2 = data9.length;
for(let i2=0; i2<len2; i2++){
const _errs22 = errors;
if(!(validate125(data9[i2], {instancePath:instancePath+"/conversations/" + i2,parentData:data9,parentDataProperty:i2,rootData,dynamicAnchors}))){
vErrors = vErrors === null ? validate125.errors : vErrors.concat(validate125.errors);
errors = vErrors.length;
}
var valid5 = _errs22 === errors;
if(!valid5){
break;
}
}
}
else {
validate124.errors = [{instancePath:instancePath+"/conversations",schemaPath:"#/properties/conversations/type",keyword:"type",params:{type: "array"},message:"must be array"}];
return false;
}
}
var valid0 = _errs20 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.inputHistory !== undefined){
let data11 = data.inputHistory;
const _errs23 = errors;
if(errors === _errs23){
if(Array.isArray(data11)){
var valid6 = true;
const len3 = data11.length;
for(let i3=0; i3<len3; i3++){
let data12 = data11[i3];
const _errs25 = errors;
const _errs26 = errors;
if(errors === _errs26){
if(data12 && typeof data12 == "object" && !Array.isArray(data12)){
let missing2;
if((data12.text === undefined) && (missing2 = "text")){
validate124.errors = [{instancePath:instancePath+"/inputHistory/" + i3,schemaPath:"#/$defs/InputHistoryEntry/required",keyword:"required",params:{missingProperty: missing2},message:"must have required property '"+missing2+"'"}];
return false;
}
else {
if(data12.conversation !== undefined){
let data13 = data12.conversation;
const _errs28 = errors;
if((typeof data13 !== "string") && (data13 !== null)){
validate124.errors = [{instancePath:instancePath+"/inputHistory/" + i3+"/conversation",schemaPath:"#/$defs/InputHistoryEntry/properties/conversation/type",keyword:"type",params:{type: schema150.properties.conversation.type},message:"must be string,null"}];
return false;
}
var valid8 = _errs28 === errors;
}
else {
var valid8 = true;
}
if(valid8){
if(data12.text !== undefined){
const _errs30 = errors;
if(typeof data12.text !== "string"){
validate124.errors = [{instancePath:instancePath+"/inputHistory/" + i3+"/text",schemaPath:"#/$defs/InputHistoryEntry/properties/text/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid8 = _errs30 === errors;
}
else {
var valid8 = true;
}
}
}
}
else {
validate124.errors = [{instancePath:instancePath+"/inputHistory/" + i3,schemaPath:"#/$defs/InputHistoryEntry/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
var valid6 = _errs25 === errors;
if(!valid6){
break;
}
}
}
else {
validate124.errors = [{instancePath:instancePath+"/inputHistory",schemaPath:"#/properties/inputHistory/type",keyword:"type",params:{type: "array"},message:"must be array"}];
return false;
}
}
var valid0 = _errs23 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.instance !== undefined){
let data15 = data.instance;
const _errs32 = errors;
const _errs33 = errors;
if(errors === _errs33){
if(data15 && typeof data15 == "object" && !Array.isArray(data15)){
let missing3;
if((((((((((data15.id === undefined) && (missing3 = "id")) || ((data15.label === undefined) && (missing3 = "label"))) || ((data15.bootId === undefined) && (missing3 = "bootId"))) || ((data15.locked === undefined) && (missing3 = "locked"))) || ((data15.protocolLocked === undefined) && (missing3 = "protocolLocked"))) || ((data15.profileExists === undefined) && (missing3 = "profileExists"))) || ((data15.archiveExists === undefined) && (missing3 = "archiveExists"))) || ((data15.safetyNumber === undefined) && (missing3 = "safetyNumber"))) || ((data15.capabilities === undefined) && (missing3 = "capabilities"))){
validate124.errors = [{instancePath:instancePath+"/instance",schemaPath:"#/$defs/InstanceInfo/required",keyword:"required",params:{missingProperty: missing3},message:"must have required property '"+missing3+"'"}];
return false;
}
else {
if(data15.archiveExists !== undefined){
const _errs35 = errors;
if(typeof data15.archiveExists !== "boolean"){
validate124.errors = [{instancePath:instancePath+"/instance/archiveExists",schemaPath:"#/$defs/InstanceInfo/properties/archiveExists/type",keyword:"type",params:{type: "boolean"},message:"must be boolean"}];
return false;
}
var valid10 = _errs35 === errors;
}
else {
var valid10 = true;
}
if(valid10){
if(data15.bootId !== undefined){
const _errs37 = errors;
if(typeof data15.bootId !== "string"){
validate124.errors = [{instancePath:instancePath+"/instance/bootId",schemaPath:"#/$defs/InstanceInfo/properties/bootId/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid10 = _errs37 === errors;
}
else {
var valid10 = true;
}
if(valid10){
if(data15.capabilities !== undefined){
let data18 = data15.capabilities;
const _errs39 = errors;
if(errors === _errs39){
if(Array.isArray(data18)){
var valid11 = true;
const len4 = data18.length;
for(let i4=0; i4<len4; i4++){
const _errs41 = errors;
if(typeof data18[i4] !== "string"){
validate124.errors = [{instancePath:instancePath+"/instance/capabilities/" + i4,schemaPath:"#/$defs/InstanceInfo/properties/capabilities/items/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid11 = _errs41 === errors;
if(!valid11){
break;
}
}
}
else {
validate124.errors = [{instancePath:instancePath+"/instance/capabilities",schemaPath:"#/$defs/InstanceInfo/properties/capabilities/type",keyword:"type",params:{type: "array"},message:"must be array"}];
return false;
}
}
var valid10 = _errs39 === errors;
}
else {
var valid10 = true;
}
if(valid10){
if(data15.id !== undefined){
const _errs43 = errors;
if(typeof data15.id !== "string"){
validate124.errors = [{instancePath:instancePath+"/instance/id",schemaPath:"#/$defs/InstanceInfo/properties/id/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid10 = _errs43 === errors;
}
else {
var valid10 = true;
}
if(valid10){
if(data15.label !== undefined){
const _errs45 = errors;
if(typeof data15.label !== "string"){
validate124.errors = [{instancePath:instancePath+"/instance/label",schemaPath:"#/$defs/InstanceInfo/properties/label/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid10 = _errs45 === errors;
}
else {
var valid10 = true;
}
if(valid10){
if(data15.locked !== undefined){
const _errs47 = errors;
if(typeof data15.locked !== "boolean"){
validate124.errors = [{instancePath:instancePath+"/instance/locked",schemaPath:"#/$defs/InstanceInfo/properties/locked/type",keyword:"type",params:{type: "boolean"},message:"must be boolean"}];
return false;
}
var valid10 = _errs47 === errors;
}
else {
var valid10 = true;
}
if(valid10){
if(data15.profileExists !== undefined){
const _errs49 = errors;
if(typeof data15.profileExists !== "boolean"){
validate124.errors = [{instancePath:instancePath+"/instance/profileExists",schemaPath:"#/$defs/InstanceInfo/properties/profileExists/type",keyword:"type",params:{type: "boolean"},message:"must be boolean"}];
return false;
}
var valid10 = _errs49 === errors;
}
else {
var valid10 = true;
}
if(valid10){
if(data15.protocolLocked !== undefined){
const _errs51 = errors;
if(typeof data15.protocolLocked !== "boolean"){
validate124.errors = [{instancePath:instancePath+"/instance/protocolLocked",schemaPath:"#/$defs/InstanceInfo/properties/protocolLocked/type",keyword:"type",params:{type: "boolean"},message:"must be boolean"}];
return false;
}
var valid10 = _errs51 === errors;
}
else {
var valid10 = true;
}
if(valid10){
if(data15.safetyNumber !== undefined){
const _errs53 = errors;
if(typeof data15.safetyNumber !== "string"){
validate124.errors = [{instancePath:instancePath+"/instance/safetyNumber",schemaPath:"#/$defs/InstanceInfo/properties/safetyNumber/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid10 = _errs53 === errors;
}
else {
var valid10 = true;
}
}
}
}
}
}
}
}
}
}
}
else {
validate124.errors = [{instancePath:instancePath+"/instance",schemaPath:"#/$defs/InstanceInfo/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
var valid0 = _errs32 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.operations !== undefined){
let data26 = data.operations;
const _errs55 = errors;
if((!(Array.isArray(data26))) && (data26 !== null)){
validate124.errors = [{instancePath:instancePath+"/operations",schemaPath:"#/properties/operations/type",keyword:"type",params:{type: schema144.properties.operations.type},message:"must be array,null"}];
return false;
}
if(errors === _errs55){
if(Array.isArray(data26)){
var valid12 = true;
const len5 = data26.length;
for(let i5=0; i5<len5; i5++){
const _errs57 = errors;
if(!(validate127(data26[i5], {instancePath:instancePath+"/operations/" + i5,parentData:data26,parentDataProperty:i5,rootData,dynamicAnchors}))){
vErrors = vErrors === null ? validate127.errors : vErrors.concat(validate127.errors);
errors = vErrors.length;
}
var valid12 = _errs57 === errors;
if(!valid12){
break;
}
}
}
}
var valid0 = _errs55 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.presenceEnabled !== undefined){
let data28 = data.presenceEnabled;
const _errs58 = errors;
if((typeof data28 !== "boolean") && (data28 !== null)){
validate124.errors = [{instancePath:instancePath+"/presenceEnabled",schemaPath:"#/properties/presenceEnabled/type",keyword:"type",params:{type: schema144.properties.presenceEnabled.type},message:"must be boolean,null"}];
return false;
}
var valid0 = _errs58 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.providerErrors !== undefined){
let data29 = data.providerErrors;
const _errs60 = errors;
if(errors === _errs60){
if(Array.isArray(data29)){
var valid13 = true;
const len6 = data29.length;
for(let i6=0; i6<len6; i6++){
let data30 = data29[i6];
const _errs62 = errors;
const _errs63 = errors;
if(errors === _errs63){
if(data30 && typeof data30 == "object" && !Array.isArray(data30)){
let missing4;
if(((((data30.id === undefined) && (missing4 = "id")) || ((data30.code === undefined) && (missing4 = "code"))) || ((data30.message === undefined) && (missing4 = "message"))) || ((data30.retryable === undefined) && (missing4 = "retryable"))){
validate124.errors = [{instancePath:instancePath+"/providerErrors/" + i6,schemaPath:"#/$defs/ProviderStatus/required",keyword:"required",params:{missingProperty: missing4},message:"must have required property '"+missing4+"'"}];
return false;
}
else {
if(data30.code !== undefined){
const _errs65 = errors;
if(typeof data30.code !== "string"){
validate124.errors = [{instancePath:instancePath+"/providerErrors/" + i6+"/code",schemaPath:"#/$defs/ProviderStatus/properties/code/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid15 = _errs65 === errors;
}
else {
var valid15 = true;
}
if(valid15){
if(data30.id !== undefined){
const _errs67 = errors;
if(typeof data30.id !== "string"){
validate124.errors = [{instancePath:instancePath+"/providerErrors/" + i6+"/id",schemaPath:"#/$defs/ProviderStatus/properties/id/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid15 = _errs67 === errors;
}
else {
var valid15 = true;
}
if(valid15){
if(data30.message !== undefined){
const _errs69 = errors;
if(typeof data30.message !== "string"){
validate124.errors = [{instancePath:instancePath+"/providerErrors/" + i6+"/message",schemaPath:"#/$defs/ProviderStatus/properties/message/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid15 = _errs69 === errors;
}
else {
var valid15 = true;
}
if(valid15){
if(data30.retryable !== undefined){
const _errs71 = errors;
if(typeof data30.retryable !== "boolean"){
validate124.errors = [{instancePath:instancePath+"/providerErrors/" + i6+"/retryable",schemaPath:"#/$defs/ProviderStatus/properties/retryable/type",keyword:"type",params:{type: "boolean"},message:"must be boolean"}];
return false;
}
var valid15 = _errs71 === errors;
}
else {
var valid15 = true;
}
}
}
}
}
}
else {
validate124.errors = [{instancePath:instancePath+"/providerErrors/" + i6,schemaPath:"#/$defs/ProviderStatus/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
var valid13 = _errs62 === errors;
if(!valid13){
break;
}
}
}
else {
validate124.errors = [{instancePath:instancePath+"/providerErrors",schemaPath:"#/properties/providerErrors/type",keyword:"type",params:{type: "array"},message:"must be array"}];
return false;
}
}
var valid0 = _errs60 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.revision !== undefined){
const _errs73 = errors;
if(typeof data.revision !== "string"){
validate124.errors = [{instancePath:instancePath+"/revision",schemaPath:"#/properties/revision/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs73 === errors;
}
else {
var valid0 = true;
}
}
}
}
}
}
}
}
}
}
}
else {
validate124.errors = [{instancePath,schemaPath:"#/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
validate124.errors = vErrors;
return errors === 0;
}
validate124.evaluated = {"props":{"activity":true,"commandHistory":true,"conversations":true,"inputHistory":true,"instance":true,"operations":true,"presenceEnabled":true,"providerErrors":true,"revision":true},"dynamicProps":false,"dynamicItems":false};

export const snapshot_error = validate131;
const schema157 = {"$schema":"https://json-schema.org/draft/2020-12/schema","additionalProperties":false,"properties":{"code":{"type":"string"},"message":{"type":"string"}},"required":["code","message"],"title":"ChatError","type":"object"};

function validate131(data, {instancePath="", parentData, parentDataProperty, rootData=data, dynamicAnchors={}}={}){
let vErrors = null;
let errors = 0;
const evaluated0 = validate131.evaluated;
if(evaluated0.dynamicProps){
evaluated0.props = undefined;
}
if(evaluated0.dynamicItems){
evaluated0.items = undefined;
}
if(errors === 0){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing0;
if(((data.code === undefined) && (missing0 = "code")) || ((data.message === undefined) && (missing0 = "message"))){
validate131.errors = [{instancePath,schemaPath:"#/required",keyword:"required",params:{missingProperty: missing0},message:"must have required property '"+missing0+"'"}];
return false;
}
else {
const _errs1 = errors;
for(const key0 in data){
if(!((key0 === "code") || (key0 === "message"))){
validate131.errors = [{instancePath,schemaPath:"#/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key0},message:"must NOT have additional properties"}];
return false;
break;
}
}
if(_errs1 === errors){
if(data.code !== undefined){
const _errs2 = errors;
if(typeof data.code !== "string"){
validate131.errors = [{instancePath:instancePath+"/code",schemaPath:"#/properties/code/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs2 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.message !== undefined){
const _errs4 = errors;
if(typeof data.message !== "string"){
validate131.errors = [{instancePath:instancePath+"/message",schemaPath:"#/properties/message/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs4 === errors;
}
else {
var valid0 = true;
}
}
}
}
}
else {
validate131.errors = [{instancePath,schemaPath:"#/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
validate131.errors = vErrors;
return errors === 0;
}
validate131.evaluated = {"props":true,"dynamicProps":false,"dynamicItems":false};

export const network_status_args = validate132;
const schema158 = {"$schema":"https://json-schema.org/draft/2020-12/schema","additionalProperties":false,"title":"ChatNetworkStatusArgs","type":"object"};

function validate132(data, {instancePath="", parentData, parentDataProperty, rootData=data, dynamicAnchors={}}={}){
let vErrors = null;
let errors = 0;
const evaluated0 = validate132.evaluated;
if(evaluated0.dynamicProps){
evaluated0.props = undefined;
}
if(evaluated0.dynamicItems){
evaluated0.items = undefined;
}
if(errors === 0){
if(data && typeof data == "object" && !Array.isArray(data)){
for(const key0 in data){
validate132.errors = [{instancePath,schemaPath:"#/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key0},message:"must NOT have additional properties"}];
return false;
break;
}
}
else {
validate132.errors = [{instancePath,schemaPath:"#/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
validate132.errors = vErrors;
return errors === 0;
}
validate132.evaluated = {"props":true,"dynamicProps":false,"dynamicItems":false};

export const network_status_output = validate133;
const schema159 = {"$defs":{"NetworkState":{"description":"Public connection progress; never contains invitations or private routing cards.","enum":["locked","local_only","invitation_required","connecting","connected","reconnecting","invitation_expired","unavailable"],"type":"string"}},"$schema":"https://json-schema.org/draft/2020-12/schema","properties":{"message":{"type":"string"},"state":{"$ref":"#/$defs/NetworkState"}},"required":["state","message"],"title":"NetworkStatus","type":"object"};
const schema160 = {"description":"Public connection progress; never contains invitations or private routing cards.","enum":["locked","local_only","invitation_required","connecting","connected","reconnecting","invitation_expired","unavailable"],"type":"string"};

function validate133(data, {instancePath="", parentData, parentDataProperty, rootData=data, dynamicAnchors={}}={}){
let vErrors = null;
let errors = 0;
const evaluated0 = validate133.evaluated;
if(evaluated0.dynamicProps){
evaluated0.props = undefined;
}
if(evaluated0.dynamicItems){
evaluated0.items = undefined;
}
if(errors === 0){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing0;
if(((data.state === undefined) && (missing0 = "state")) || ((data.message === undefined) && (missing0 = "message"))){
validate133.errors = [{instancePath,schemaPath:"#/required",keyword:"required",params:{missingProperty: missing0},message:"must have required property '"+missing0+"'"}];
return false;
}
else {
if(data.message !== undefined){
const _errs1 = errors;
if(typeof data.message !== "string"){
validate133.errors = [{instancePath:instancePath+"/message",schemaPath:"#/properties/message/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs1 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.state !== undefined){
let data1 = data.state;
const _errs3 = errors;
if(typeof data1 !== "string"){
validate133.errors = [{instancePath:instancePath+"/state",schemaPath:"#/$defs/NetworkState/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
if(!((((((((data1 === "locked") || (data1 === "local_only")) || (data1 === "invitation_required")) || (data1 === "connecting")) || (data1 === "connected")) || (data1 === "reconnecting")) || (data1 === "invitation_expired")) || (data1 === "unavailable"))){
validate133.errors = [{instancePath:instancePath+"/state",schemaPath:"#/$defs/NetworkState/enum",keyword:"enum",params:{allowedValues: schema160.enum},message:"must be equal to one of the allowed values"}];
return false;
}
var valid0 = _errs3 === errors;
}
else {
var valid0 = true;
}
}
}
}
else {
validate133.errors = [{instancePath,schemaPath:"#/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
validate133.errors = vErrors;
return errors === 0;
}
validate133.evaluated = {"props":{"message":true,"state":true},"dynamicProps":false,"dynamicItems":false};

export const network_status_error = validate134;
const schema161 = {"$schema":"https://json-schema.org/draft/2020-12/schema","additionalProperties":false,"properties":{"code":{"type":"string"},"message":{"type":"string"}},"required":["code","message"],"title":"ChatError","type":"object"};

function validate134(data, {instancePath="", parentData, parentDataProperty, rootData=data, dynamicAnchors={}}={}){
let vErrors = null;
let errors = 0;
const evaluated0 = validate134.evaluated;
if(evaluated0.dynamicProps){
evaluated0.props = undefined;
}
if(evaluated0.dynamicItems){
evaluated0.items = undefined;
}
if(errors === 0){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing0;
if(((data.code === undefined) && (missing0 = "code")) || ((data.message === undefined) && (missing0 = "message"))){
validate134.errors = [{instancePath,schemaPath:"#/required",keyword:"required",params:{missingProperty: missing0},message:"must have required property '"+missing0+"'"}];
return false;
}
else {
const _errs1 = errors;
for(const key0 in data){
if(!((key0 === "code") || (key0 === "message"))){
validate134.errors = [{instancePath,schemaPath:"#/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key0},message:"must NOT have additional properties"}];
return false;
break;
}
}
if(_errs1 === errors){
if(data.code !== undefined){
const _errs2 = errors;
if(typeof data.code !== "string"){
validate134.errors = [{instancePath:instancePath+"/code",schemaPath:"#/properties/code/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs2 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.message !== undefined){
const _errs4 = errors;
if(typeof data.message !== "string"){
validate134.errors = [{instancePath:instancePath+"/message",schemaPath:"#/properties/message/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs4 === errors;
}
else {
var valid0 = true;
}
}
}
}
}
else {
validate134.errors = [{instancePath,schemaPath:"#/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
validate134.errors = vErrors;
return errors === 0;
}
validate134.evaluated = {"props":true,"dynamicProps":false,"dynamicItems":false};

export const import_network_invitation_args = validate135;
const schema162 = {"$schema":"https://json-schema.org/draft/2020-12/schema","additionalProperties":false,"properties":{"code":{"type":"string"}},"required":["code"],"title":"ChatImportNetworkInvitationArgs","type":"object"};

function validate135(data, {instancePath="", parentData, parentDataProperty, rootData=data, dynamicAnchors={}}={}){
let vErrors = null;
let errors = 0;
const evaluated0 = validate135.evaluated;
if(evaluated0.dynamicProps){
evaluated0.props = undefined;
}
if(evaluated0.dynamicItems){
evaluated0.items = undefined;
}
if(errors === 0){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing0;
if((data.code === undefined) && (missing0 = "code")){
validate135.errors = [{instancePath,schemaPath:"#/required",keyword:"required",params:{missingProperty: missing0},message:"must have required property '"+missing0+"'"}];
return false;
}
else {
const _errs1 = errors;
for(const key0 in data){
if(!(key0 === "code")){
validate135.errors = [{instancePath,schemaPath:"#/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key0},message:"must NOT have additional properties"}];
return false;
break;
}
}
if(_errs1 === errors){
if(data.code !== undefined){
if(typeof data.code !== "string"){
validate135.errors = [{instancePath:instancePath+"/code",schemaPath:"#/properties/code/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
}
}
}
}
else {
validate135.errors = [{instancePath,schemaPath:"#/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
validate135.errors = vErrors;
return errors === 0;
}
validate135.evaluated = {"props":true,"dynamicProps":false,"dynamicItems":false};

export const import_network_invitation_output = validate136;
const schema163 = {"$defs":{"NetworkState":{"description":"Public connection progress; never contains invitations or private routing cards.","enum":["locked","local_only","invitation_required","connecting","connected","reconnecting","invitation_expired","unavailable"],"type":"string"}},"$schema":"https://json-schema.org/draft/2020-12/schema","properties":{"message":{"type":"string"},"state":{"$ref":"#/$defs/NetworkState"}},"required":["state","message"],"title":"NetworkStatus","type":"object"};
const schema164 = {"description":"Public connection progress; never contains invitations or private routing cards.","enum":["locked","local_only","invitation_required","connecting","connected","reconnecting","invitation_expired","unavailable"],"type":"string"};

function validate136(data, {instancePath="", parentData, parentDataProperty, rootData=data, dynamicAnchors={}}={}){
let vErrors = null;
let errors = 0;
const evaluated0 = validate136.evaluated;
if(evaluated0.dynamicProps){
evaluated0.props = undefined;
}
if(evaluated0.dynamicItems){
evaluated0.items = undefined;
}
if(errors === 0){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing0;
if(((data.state === undefined) && (missing0 = "state")) || ((data.message === undefined) && (missing0 = "message"))){
validate136.errors = [{instancePath,schemaPath:"#/required",keyword:"required",params:{missingProperty: missing0},message:"must have required property '"+missing0+"'"}];
return false;
}
else {
if(data.message !== undefined){
const _errs1 = errors;
if(typeof data.message !== "string"){
validate136.errors = [{instancePath:instancePath+"/message",schemaPath:"#/properties/message/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs1 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.state !== undefined){
let data1 = data.state;
const _errs3 = errors;
if(typeof data1 !== "string"){
validate136.errors = [{instancePath:instancePath+"/state",schemaPath:"#/$defs/NetworkState/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
if(!((((((((data1 === "locked") || (data1 === "local_only")) || (data1 === "invitation_required")) || (data1 === "connecting")) || (data1 === "connected")) || (data1 === "reconnecting")) || (data1 === "invitation_expired")) || (data1 === "unavailable"))){
validate136.errors = [{instancePath:instancePath+"/state",schemaPath:"#/$defs/NetworkState/enum",keyword:"enum",params:{allowedValues: schema164.enum},message:"must be equal to one of the allowed values"}];
return false;
}
var valid0 = _errs3 === errors;
}
else {
var valid0 = true;
}
}
}
}
else {
validate136.errors = [{instancePath,schemaPath:"#/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
validate136.errors = vErrors;
return errors === 0;
}
validate136.evaluated = {"props":{"message":true,"state":true},"dynamicProps":false,"dynamicItems":false};

export const import_network_invitation_error = validate137;
const schema165 = {"$schema":"https://json-schema.org/draft/2020-12/schema","additionalProperties":false,"properties":{"code":{"type":"string"},"message":{"type":"string"}},"required":["code","message"],"title":"ChatError","type":"object"};

function validate137(data, {instancePath="", parentData, parentDataProperty, rootData=data, dynamicAnchors={}}={}){
let vErrors = null;
let errors = 0;
const evaluated0 = validate137.evaluated;
if(evaluated0.dynamicProps){
evaluated0.props = undefined;
}
if(evaluated0.dynamicItems){
evaluated0.items = undefined;
}
if(errors === 0){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing0;
if(((data.code === undefined) && (missing0 = "code")) || ((data.message === undefined) && (missing0 = "message"))){
validate137.errors = [{instancePath,schemaPath:"#/required",keyword:"required",params:{missingProperty: missing0},message:"must have required property '"+missing0+"'"}];
return false;
}
else {
const _errs1 = errors;
for(const key0 in data){
if(!((key0 === "code") || (key0 === "message"))){
validate137.errors = [{instancePath,schemaPath:"#/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key0},message:"must NOT have additional properties"}];
return false;
break;
}
}
if(_errs1 === errors){
if(data.code !== undefined){
const _errs2 = errors;
if(typeof data.code !== "string"){
validate137.errors = [{instancePath:instancePath+"/code",schemaPath:"#/properties/code/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs2 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.message !== undefined){
const _errs4 = errors;
if(typeof data.message !== "string"){
validate137.errors = [{instancePath:instancePath+"/message",schemaPath:"#/properties/message/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs4 === errors;
}
else {
var valid0 = true;
}
}
}
}
}
else {
validate137.errors = [{instancePath,schemaPath:"#/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
validate137.errors = vErrors;
return errors === 0;
}
validate137.evaluated = {"props":true,"dynamicProps":false,"dynamicItems":false};

export const catalogue_args = validate138;
const schema166 = {"$schema":"https://json-schema.org/draft/2020-12/schema","additionalProperties":false,"properties":{"conversation":{"type":["string","null"]}},"title":"ChatCatalogueArgs","type":"object"};

function validate138(data, {instancePath="", parentData, parentDataProperty, rootData=data, dynamicAnchors={}}={}){
let vErrors = null;
let errors = 0;
const evaluated0 = validate138.evaluated;
if(evaluated0.dynamicProps){
evaluated0.props = undefined;
}
if(evaluated0.dynamicItems){
evaluated0.items = undefined;
}
if(errors === 0){
if(data && typeof data == "object" && !Array.isArray(data)){
const _errs1 = errors;
for(const key0 in data){
if(!(key0 === "conversation")){
validate138.errors = [{instancePath,schemaPath:"#/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key0},message:"must NOT have additional properties"}];
return false;
break;
}
}
if(_errs1 === errors){
if(data.conversation !== undefined){
let data0 = data.conversation;
if((typeof data0 !== "string") && (data0 !== null)){
validate138.errors = [{instancePath:instancePath+"/conversation",schemaPath:"#/properties/conversation/type",keyword:"type",params:{type: schema166.properties.conversation.type},message:"must be string,null"}];
return false;
}
}
}
}
else {
validate138.errors = [{instancePath,schemaPath:"#/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
validate138.errors = vErrors;
return errors === 0;
}
validate138.evaluated = {"props":true,"dynamicProps":false,"dynamicItems":false};

export const catalogue_output = validate139;
const schema167 = {"$defs":{"CommandSpec":{"properties":{"available":{"type":"boolean"},"capability":{"type":["string","null"]},"description":{"type":"string"},"name":{"type":"string"},"scope":{"type":"string"},"usage":{"type":"string"}},"required":["name","usage","description","scope","available"],"type":"object"}},"$schema":"https://json-schema.org/draft/2020-12/schema","items":{"$ref":"#/$defs/CommandSpec"},"title":"Array_of_CommandSpec","type":"array"};
const schema168 = {"properties":{"available":{"type":"boolean"},"capability":{"type":["string","null"]},"description":{"type":"string"},"name":{"type":"string"},"scope":{"type":"string"},"usage":{"type":"string"}},"required":["name","usage","description","scope","available"],"type":"object"};

function validate139(data, {instancePath="", parentData, parentDataProperty, rootData=data, dynamicAnchors={}}={}){
let vErrors = null;
let errors = 0;
const evaluated0 = validate139.evaluated;
if(evaluated0.dynamicProps){
evaluated0.props = undefined;
}
if(evaluated0.dynamicItems){
evaluated0.items = undefined;
}
if(errors === 0){
if(Array.isArray(data)){
var valid0 = true;
const len0 = data.length;
for(let i0=0; i0<len0; i0++){
let data0 = data[i0];
const _errs1 = errors;
const _errs2 = errors;
if(errors === _errs2){
if(data0 && typeof data0 == "object" && !Array.isArray(data0)){
let missing0;
if((((((data0.name === undefined) && (missing0 = "name")) || ((data0.usage === undefined) && (missing0 = "usage"))) || ((data0.description === undefined) && (missing0 = "description"))) || ((data0.scope === undefined) && (missing0 = "scope"))) || ((data0.available === undefined) && (missing0 = "available"))){
validate139.errors = [{instancePath:instancePath+"/" + i0,schemaPath:"#/$defs/CommandSpec/required",keyword:"required",params:{missingProperty: missing0},message:"must have required property '"+missing0+"'"}];
return false;
}
else {
if(data0.available !== undefined){
const _errs4 = errors;
if(typeof data0.available !== "boolean"){
validate139.errors = [{instancePath:instancePath+"/" + i0+"/available",schemaPath:"#/$defs/CommandSpec/properties/available/type",keyword:"type",params:{type: "boolean"},message:"must be boolean"}];
return false;
}
var valid2 = _errs4 === errors;
}
else {
var valid2 = true;
}
if(valid2){
if(data0.capability !== undefined){
let data2 = data0.capability;
const _errs6 = errors;
if((typeof data2 !== "string") && (data2 !== null)){
validate139.errors = [{instancePath:instancePath+"/" + i0+"/capability",schemaPath:"#/$defs/CommandSpec/properties/capability/type",keyword:"type",params:{type: schema168.properties.capability.type},message:"must be string,null"}];
return false;
}
var valid2 = _errs6 === errors;
}
else {
var valid2 = true;
}
if(valid2){
if(data0.description !== undefined){
const _errs8 = errors;
if(typeof data0.description !== "string"){
validate139.errors = [{instancePath:instancePath+"/" + i0+"/description",schemaPath:"#/$defs/CommandSpec/properties/description/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid2 = _errs8 === errors;
}
else {
var valid2 = true;
}
if(valid2){
if(data0.name !== undefined){
const _errs10 = errors;
if(typeof data0.name !== "string"){
validate139.errors = [{instancePath:instancePath+"/" + i0+"/name",schemaPath:"#/$defs/CommandSpec/properties/name/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid2 = _errs10 === errors;
}
else {
var valid2 = true;
}
if(valid2){
if(data0.scope !== undefined){
const _errs12 = errors;
if(typeof data0.scope !== "string"){
validate139.errors = [{instancePath:instancePath+"/" + i0+"/scope",schemaPath:"#/$defs/CommandSpec/properties/scope/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid2 = _errs12 === errors;
}
else {
var valid2 = true;
}
if(valid2){
if(data0.usage !== undefined){
const _errs14 = errors;
if(typeof data0.usage !== "string"){
validate139.errors = [{instancePath:instancePath+"/" + i0+"/usage",schemaPath:"#/$defs/CommandSpec/properties/usage/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid2 = _errs14 === errors;
}
else {
var valid2 = true;
}
}
}
}
}
}
}
}
else {
validate139.errors = [{instancePath:instancePath+"/" + i0,schemaPath:"#/$defs/CommandSpec/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
var valid0 = _errs1 === errors;
if(!valid0){
break;
}
}
}
else {
validate139.errors = [{instancePath,schemaPath:"#/type",keyword:"type",params:{type: "array"},message:"must be array"}];
return false;
}
}
validate139.errors = vErrors;
return errors === 0;
}
validate139.evaluated = {"items":true,"dynamicProps":false,"dynamicItems":false};

export const catalogue_error = validate140;
const schema169 = {"$schema":"https://json-schema.org/draft/2020-12/schema","additionalProperties":false,"properties":{"code":{"type":"string"},"message":{"type":"string"}},"required":["code","message"],"title":"ChatError","type":"object"};

function validate140(data, {instancePath="", parentData, parentDataProperty, rootData=data, dynamicAnchors={}}={}){
let vErrors = null;
let errors = 0;
const evaluated0 = validate140.evaluated;
if(evaluated0.dynamicProps){
evaluated0.props = undefined;
}
if(evaluated0.dynamicItems){
evaluated0.items = undefined;
}
if(errors === 0){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing0;
if(((data.code === undefined) && (missing0 = "code")) || ((data.message === undefined) && (missing0 = "message"))){
validate140.errors = [{instancePath,schemaPath:"#/required",keyword:"required",params:{missingProperty: missing0},message:"must have required property '"+missing0+"'"}];
return false;
}
else {
const _errs1 = errors;
for(const key0 in data){
if(!((key0 === "code") || (key0 === "message"))){
validate140.errors = [{instancePath,schemaPath:"#/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key0},message:"must NOT have additional properties"}];
return false;
break;
}
}
if(_errs1 === errors){
if(data.code !== undefined){
const _errs2 = errors;
if(typeof data.code !== "string"){
validate140.errors = [{instancePath:instancePath+"/code",schemaPath:"#/properties/code/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs2 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.message !== undefined){
const _errs4 = errors;
if(typeof data.message !== "string"){
validate140.errors = [{instancePath:instancePath+"/message",schemaPath:"#/properties/message/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs4 === errors;
}
else {
var valid0 = true;
}
}
}
}
}
else {
validate140.errors = [{instancePath,schemaPath:"#/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
validate140.errors = vErrors;
return errors === 0;
}
validate140.evaluated = {"props":true,"dynamicProps":false,"dynamicItems":false};

export const history_args = validate141;
const schema170 = {"$schema":"https://json-schema.org/draft/2020-12/schema","additionalProperties":false,"properties":{"before":{"type":["string","null"]},"conversation":{"type":"string"},"limit":{"format":"uint16","maximum":65535,"minimum":0,"type":"integer"}},"required":["conversation","limit"],"title":"ChatHistoryArgs","type":"object"};

function validate141(data, {instancePath="", parentData, parentDataProperty, rootData=data, dynamicAnchors={}}={}){
let vErrors = null;
let errors = 0;
const evaluated0 = validate141.evaluated;
if(evaluated0.dynamicProps){
evaluated0.props = undefined;
}
if(evaluated0.dynamicItems){
evaluated0.items = undefined;
}
if(errors === 0){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing0;
if(((data.conversation === undefined) && (missing0 = "conversation")) || ((data.limit === undefined) && (missing0 = "limit"))){
validate141.errors = [{instancePath,schemaPath:"#/required",keyword:"required",params:{missingProperty: missing0},message:"must have required property '"+missing0+"'"}];
return false;
}
else {
const _errs1 = errors;
for(const key0 in data){
if(!(((key0 === "before") || (key0 === "conversation")) || (key0 === "limit"))){
validate141.errors = [{instancePath,schemaPath:"#/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key0},message:"must NOT have additional properties"}];
return false;
break;
}
}
if(_errs1 === errors){
if(data.before !== undefined){
let data0 = data.before;
const _errs2 = errors;
if((typeof data0 !== "string") && (data0 !== null)){
validate141.errors = [{instancePath:instancePath+"/before",schemaPath:"#/properties/before/type",keyword:"type",params:{type: schema170.properties.before.type},message:"must be string,null"}];
return false;
}
var valid0 = _errs2 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.conversation !== undefined){
const _errs4 = errors;
if(typeof data.conversation !== "string"){
validate141.errors = [{instancePath:instancePath+"/conversation",schemaPath:"#/properties/conversation/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs4 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.limit !== undefined){
let data2 = data.limit;
const _errs6 = errors;
if(!(((typeof data2 == "number") && (!(data2 % 1) && !isNaN(data2))) && (isFinite(data2)))){
validate141.errors = [{instancePath:instancePath+"/limit",schemaPath:"#/properties/limit/type",keyword:"type",params:{type: "integer"},message:"must be integer"}];
return false;
}
if(errors === _errs6){
if((typeof data2 == "number") && (isFinite(data2))){
if(data2 > 65535 || isNaN(data2)){
validate141.errors = [{instancePath:instancePath+"/limit",schemaPath:"#/properties/limit/maximum",keyword:"maximum",params:{comparison: "<=", limit: 65535},message:"must be <= 65535"}];
return false;
}
else {
if(data2 < 0 || isNaN(data2)){
validate141.errors = [{instancePath:instancePath+"/limit",schemaPath:"#/properties/limit/minimum",keyword:"minimum",params:{comparison: ">=", limit: 0},message:"must be >= 0"}];
return false;
}
}
}
}
var valid0 = _errs6 === errors;
}
else {
var valid0 = true;
}
}
}
}
}
}
else {
validate141.errors = [{instancePath,schemaPath:"#/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
validate141.errors = vErrors;
return errors === 0;
}
validate141.evaluated = {"props":true,"dynamicProps":false,"dynamicItems":false};

export const history_output = validate142;
const schema171 = {"$defs":{"ActionResult":{"properties":{"artifacts":{"items":{"$ref":"#/$defs/Artifact"},"type":"array"},"details":{"items":{"type":"string"},"type":"array"},"id":{"type":"string"},"messageId":{"default":null,"type":["string","null"]},"outputBase64":{"description":"Exact signed bytes, base64 encoded; views decode only for display.","type":["string","null"]},"state":{"type":"string"},"stderr":{"type":"boolean"}},"required":["id","state","stderr","details","artifacts"],"type":"object"},"Artifact":{"properties":{"name":{"type":"string"},"url":{"type":"string"}},"required":["name","url"],"type":"object"},"Delivery":{"enum":["local_accepted","delivered"],"type":"string"},"Message":{"properties":{"body":{"type":"string"},"conversationId":{"type":"string"},"delivery":{"anyOf":[{"$ref":"#/$defs/Delivery"},{"type":"null"}],"description":"Delivered is an authenticated recipient acknowledgement, never a read receipt."},"id":{"type":"string"},"memberId":{"type":["string","null"]},"mine":{"type":"boolean"},"nickname":{"type":"string"},"operationId":{"default":null,"type":["string","null"]},"result":{"anyOf":[{"$ref":"#/$defs/ActionResult"},{"type":"null"}],"default":null},"timestamp":{"format":"uint64","minimum":0,"type":"integer"}},"required":["id","conversationId","nickname","body","timestamp","mine"],"type":"object"}},"$schema":"https://json-schema.org/draft/2020-12/schema","properties":{"before":{"type":["string","null"]},"messages":{"items":{"$ref":"#/$defs/Message"},"type":"array"}},"required":["messages"],"title":"HistoryPage","type":"object"};
const schema172 = {"properties":{"body":{"type":"string"},"conversationId":{"type":"string"},"delivery":{"anyOf":[{"$ref":"#/$defs/Delivery"},{"type":"null"}],"description":"Delivered is an authenticated recipient acknowledgement, never a read receipt."},"id":{"type":"string"},"memberId":{"type":["string","null"]},"mine":{"type":"boolean"},"nickname":{"type":"string"},"operationId":{"default":null,"type":["string","null"]},"result":{"anyOf":[{"$ref":"#/$defs/ActionResult"},{"type":"null"}],"default":null},"timestamp":{"format":"uint64","minimum":0,"type":"integer"}},"required":["id","conversationId","nickname","body","timestamp","mine"],"type":"object"};
const schema173 = {"enum":["local_accepted","delivered"],"type":"string"};
const schema174 = {"properties":{"artifacts":{"items":{"$ref":"#/$defs/Artifact"},"type":"array"},"details":{"items":{"type":"string"},"type":"array"},"id":{"type":"string"},"messageId":{"default":null,"type":["string","null"]},"outputBase64":{"description":"Exact signed bytes, base64 encoded; views decode only for display.","type":["string","null"]},"state":{"type":"string"},"stderr":{"type":"boolean"}},"required":["id","state","stderr","details","artifacts"],"type":"object"};
const schema175 = {"properties":{"name":{"type":"string"},"url":{"type":"string"}},"required":["name","url"],"type":"object"};

function validate144(data, {instancePath="", parentData, parentDataProperty, rootData=data, dynamicAnchors={}}={}){
let vErrors = null;
let errors = 0;
const evaluated0 = validate144.evaluated;
if(evaluated0.dynamicProps){
evaluated0.props = undefined;
}
if(evaluated0.dynamicItems){
evaluated0.items = undefined;
}
if(errors === 0){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing0;
if((((((data.id === undefined) && (missing0 = "id")) || ((data.state === undefined) && (missing0 = "state"))) || ((data.stderr === undefined) && (missing0 = "stderr"))) || ((data.details === undefined) && (missing0 = "details"))) || ((data.artifacts === undefined) && (missing0 = "artifacts"))){
validate144.errors = [{instancePath,schemaPath:"#/required",keyword:"required",params:{missingProperty: missing0},message:"must have required property '"+missing0+"'"}];
return false;
}
else {
if(data.artifacts !== undefined){
let data0 = data.artifacts;
const _errs1 = errors;
if(errors === _errs1){
if(Array.isArray(data0)){
var valid1 = true;
const len0 = data0.length;
for(let i0=0; i0<len0; i0++){
let data1 = data0[i0];
const _errs3 = errors;
const _errs4 = errors;
if(errors === _errs4){
if(data1 && typeof data1 == "object" && !Array.isArray(data1)){
let missing1;
if(((data1.name === undefined) && (missing1 = "name")) || ((data1.url === undefined) && (missing1 = "url"))){
validate144.errors = [{instancePath:instancePath+"/artifacts/" + i0,schemaPath:"#/$defs/Artifact/required",keyword:"required",params:{missingProperty: missing1},message:"must have required property '"+missing1+"'"}];
return false;
}
else {
if(data1.name !== undefined){
const _errs6 = errors;
if(typeof data1.name !== "string"){
validate144.errors = [{instancePath:instancePath+"/artifacts/" + i0+"/name",schemaPath:"#/$defs/Artifact/properties/name/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid3 = _errs6 === errors;
}
else {
var valid3 = true;
}
if(valid3){
if(data1.url !== undefined){
const _errs8 = errors;
if(typeof data1.url !== "string"){
validate144.errors = [{instancePath:instancePath+"/artifacts/" + i0+"/url",schemaPath:"#/$defs/Artifact/properties/url/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid3 = _errs8 === errors;
}
else {
var valid3 = true;
}
}
}
}
else {
validate144.errors = [{instancePath:instancePath+"/artifacts/" + i0,schemaPath:"#/$defs/Artifact/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
var valid1 = _errs3 === errors;
if(!valid1){
break;
}
}
}
else {
validate144.errors = [{instancePath:instancePath+"/artifacts",schemaPath:"#/properties/artifacts/type",keyword:"type",params:{type: "array"},message:"must be array"}];
return false;
}
}
var valid0 = _errs1 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.details !== undefined){
let data4 = data.details;
const _errs10 = errors;
if(errors === _errs10){
if(Array.isArray(data4)){
var valid4 = true;
const len1 = data4.length;
for(let i1=0; i1<len1; i1++){
const _errs12 = errors;
if(typeof data4[i1] !== "string"){
validate144.errors = [{instancePath:instancePath+"/details/" + i1,schemaPath:"#/properties/details/items/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid4 = _errs12 === errors;
if(!valid4){
break;
}
}
}
else {
validate144.errors = [{instancePath:instancePath+"/details",schemaPath:"#/properties/details/type",keyword:"type",params:{type: "array"},message:"must be array"}];
return false;
}
}
var valid0 = _errs10 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.id !== undefined){
const _errs14 = errors;
if(typeof data.id !== "string"){
validate144.errors = [{instancePath:instancePath+"/id",schemaPath:"#/properties/id/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs14 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.messageId !== undefined){
let data7 = data.messageId;
const _errs16 = errors;
if((typeof data7 !== "string") && (data7 !== null)){
validate144.errors = [{instancePath:instancePath+"/messageId",schemaPath:"#/properties/messageId/type",keyword:"type",params:{type: schema174.properties.messageId.type},message:"must be string,null"}];
return false;
}
var valid0 = _errs16 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.outputBase64 !== undefined){
let data8 = data.outputBase64;
const _errs18 = errors;
if((typeof data8 !== "string") && (data8 !== null)){
validate144.errors = [{instancePath:instancePath+"/outputBase64",schemaPath:"#/properties/outputBase64/type",keyword:"type",params:{type: schema174.properties.outputBase64.type},message:"must be string,null"}];
return false;
}
var valid0 = _errs18 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.state !== undefined){
const _errs20 = errors;
if(typeof data.state !== "string"){
validate144.errors = [{instancePath:instancePath+"/state",schemaPath:"#/properties/state/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs20 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.stderr !== undefined){
const _errs22 = errors;
if(typeof data.stderr !== "boolean"){
validate144.errors = [{instancePath:instancePath+"/stderr",schemaPath:"#/properties/stderr/type",keyword:"type",params:{type: "boolean"},message:"must be boolean"}];
return false;
}
var valid0 = _errs22 === errors;
}
else {
var valid0 = true;
}
}
}
}
}
}
}
}
}
else {
validate144.errors = [{instancePath,schemaPath:"#/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
validate144.errors = vErrors;
return errors === 0;
}
validate144.evaluated = {"props":{"artifacts":true,"details":true,"id":true,"messageId":true,"outputBase64":true,"state":true,"stderr":true},"dynamicProps":false,"dynamicItems":false};


function validate143(data, {instancePath="", parentData, parentDataProperty, rootData=data, dynamicAnchors={}}={}){
let vErrors = null;
let errors = 0;
const evaluated0 = validate143.evaluated;
if(evaluated0.dynamicProps){
evaluated0.props = undefined;
}
if(evaluated0.dynamicItems){
evaluated0.items = undefined;
}
if(errors === 0){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing0;
if(((((((data.id === undefined) && (missing0 = "id")) || ((data.conversationId === undefined) && (missing0 = "conversationId"))) || ((data.nickname === undefined) && (missing0 = "nickname"))) || ((data.body === undefined) && (missing0 = "body"))) || ((data.timestamp === undefined) && (missing0 = "timestamp"))) || ((data.mine === undefined) && (missing0 = "mine"))){
validate143.errors = [{instancePath,schemaPath:"#/required",keyword:"required",params:{missingProperty: missing0},message:"must have required property '"+missing0+"'"}];
return false;
}
else {
if(data.body !== undefined){
const _errs1 = errors;
if(typeof data.body !== "string"){
validate143.errors = [{instancePath:instancePath+"/body",schemaPath:"#/properties/body/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs1 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.conversationId !== undefined){
const _errs3 = errors;
if(typeof data.conversationId !== "string"){
validate143.errors = [{instancePath:instancePath+"/conversationId",schemaPath:"#/properties/conversationId/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs3 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.delivery !== undefined){
let data2 = data.delivery;
const _errs5 = errors;
const _errs6 = errors;
let valid1 = false;
const _errs7 = errors;
if(typeof data2 !== "string"){
const err0 = {instancePath:instancePath+"/delivery",schemaPath:"#/$defs/Delivery/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err0];
}
else {
vErrors.push(err0);
}
errors++;
}
if(!((data2 === "local_accepted") || (data2 === "delivered"))){
const err1 = {instancePath:instancePath+"/delivery",schemaPath:"#/$defs/Delivery/enum",keyword:"enum",params:{allowedValues: schema173.enum},message:"must be equal to one of the allowed values"};
if(vErrors === null){
vErrors = [err1];
}
else {
vErrors.push(err1);
}
errors++;
}
var _valid0 = _errs7 === errors;
valid1 = valid1 || _valid0;
const _errs10 = errors;
if(data2 !== null){
const err2 = {instancePath:instancePath+"/delivery",schemaPath:"#/properties/delivery/anyOf/1/type",keyword:"type",params:{type: "null"},message:"must be null"};
if(vErrors === null){
vErrors = [err2];
}
else {
vErrors.push(err2);
}
errors++;
}
var _valid0 = _errs10 === errors;
valid1 = valid1 || _valid0;
if(!valid1){
const err3 = {instancePath:instancePath+"/delivery",schemaPath:"#/properties/delivery/anyOf",keyword:"anyOf",params:{},message:"must match a schema in anyOf"};
if(vErrors === null){
vErrors = [err3];
}
else {
vErrors.push(err3);
}
errors++;
validate143.errors = vErrors;
return false;
}
else {
errors = _errs6;
if(vErrors !== null){
if(_errs6){
vErrors.length = _errs6;
}
else {
vErrors = null;
}
}
}
var valid0 = _errs5 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.id !== undefined){
const _errs12 = errors;
if(typeof data.id !== "string"){
validate143.errors = [{instancePath:instancePath+"/id",schemaPath:"#/properties/id/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs12 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.memberId !== undefined){
let data4 = data.memberId;
const _errs14 = errors;
if((typeof data4 !== "string") && (data4 !== null)){
validate143.errors = [{instancePath:instancePath+"/memberId",schemaPath:"#/properties/memberId/type",keyword:"type",params:{type: schema172.properties.memberId.type},message:"must be string,null"}];
return false;
}
var valid0 = _errs14 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.mine !== undefined){
const _errs16 = errors;
if(typeof data.mine !== "boolean"){
validate143.errors = [{instancePath:instancePath+"/mine",schemaPath:"#/properties/mine/type",keyword:"type",params:{type: "boolean"},message:"must be boolean"}];
return false;
}
var valid0 = _errs16 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.nickname !== undefined){
const _errs18 = errors;
if(typeof data.nickname !== "string"){
validate143.errors = [{instancePath:instancePath+"/nickname",schemaPath:"#/properties/nickname/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs18 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.operationId !== undefined){
let data7 = data.operationId;
const _errs20 = errors;
if((typeof data7 !== "string") && (data7 !== null)){
validate143.errors = [{instancePath:instancePath+"/operationId",schemaPath:"#/properties/operationId/type",keyword:"type",params:{type: schema172.properties.operationId.type},message:"must be string,null"}];
return false;
}
var valid0 = _errs20 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.result !== undefined){
let data8 = data.result;
const _errs22 = errors;
const _errs23 = errors;
let valid3 = false;
const _errs24 = errors;
if(!(validate144(data8, {instancePath:instancePath+"/result",parentData:data,parentDataProperty:"result",rootData,dynamicAnchors}))){
vErrors = vErrors === null ? validate144.errors : vErrors.concat(validate144.errors);
errors = vErrors.length;
}
var _valid1 = _errs24 === errors;
valid3 = valid3 || _valid1;
if(_valid1){
var props0 = {};
props0.artifacts = true;
props0.details = true;
props0.id = true;
props0.messageId = true;
props0.outputBase64 = true;
props0.state = true;
props0.stderr = true;
}
const _errs25 = errors;
if(data8 !== null){
const err4 = {instancePath:instancePath+"/result",schemaPath:"#/properties/result/anyOf/1/type",keyword:"type",params:{type: "null"},message:"must be null"};
if(vErrors === null){
vErrors = [err4];
}
else {
vErrors.push(err4);
}
errors++;
}
var _valid1 = _errs25 === errors;
valid3 = valid3 || _valid1;
if(!valid3){
const err5 = {instancePath:instancePath+"/result",schemaPath:"#/properties/result/anyOf",keyword:"anyOf",params:{},message:"must match a schema in anyOf"};
if(vErrors === null){
vErrors = [err5];
}
else {
vErrors.push(err5);
}
errors++;
validate143.errors = vErrors;
return false;
}
else {
errors = _errs23;
if(vErrors !== null){
if(_errs23){
vErrors.length = _errs23;
}
else {
vErrors = null;
}
}
}
var valid0 = _errs22 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.timestamp !== undefined){
let data9 = data.timestamp;
const _errs27 = errors;
if(!(((typeof data9 == "number") && (!(data9 % 1) && !isNaN(data9))) && (isFinite(data9)))){
validate143.errors = [{instancePath:instancePath+"/timestamp",schemaPath:"#/properties/timestamp/type",keyword:"type",params:{type: "integer"},message:"must be integer"}];
return false;
}
if(errors === _errs27){
if((typeof data9 == "number") && (isFinite(data9))){
if(data9 < 0 || isNaN(data9)){
validate143.errors = [{instancePath:instancePath+"/timestamp",schemaPath:"#/properties/timestamp/minimum",keyword:"minimum",params:{comparison: ">=", limit: 0},message:"must be >= 0"}];
return false;
}
}
}
var valid0 = _errs27 === errors;
}
else {
var valid0 = true;
}
}
}
}
}
}
}
}
}
}
}
}
else {
validate143.errors = [{instancePath,schemaPath:"#/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
validate143.errors = vErrors;
return errors === 0;
}
validate143.evaluated = {"props":{"body":true,"conversationId":true,"delivery":true,"id":true,"memberId":true,"mine":true,"nickname":true,"operationId":true,"result":true,"timestamp":true},"dynamicProps":false,"dynamicItems":false};


function validate142(data, {instancePath="", parentData, parentDataProperty, rootData=data, dynamicAnchors={}}={}){
let vErrors = null;
let errors = 0;
const evaluated0 = validate142.evaluated;
if(evaluated0.dynamicProps){
evaluated0.props = undefined;
}
if(evaluated0.dynamicItems){
evaluated0.items = undefined;
}
if(errors === 0){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing0;
if((data.messages === undefined) && (missing0 = "messages")){
validate142.errors = [{instancePath,schemaPath:"#/required",keyword:"required",params:{missingProperty: missing0},message:"must have required property '"+missing0+"'"}];
return false;
}
else {
if(data.before !== undefined){
let data0 = data.before;
const _errs1 = errors;
if((typeof data0 !== "string") && (data0 !== null)){
validate142.errors = [{instancePath:instancePath+"/before",schemaPath:"#/properties/before/type",keyword:"type",params:{type: schema171.properties.before.type},message:"must be string,null"}];
return false;
}
var valid0 = _errs1 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.messages !== undefined){
let data1 = data.messages;
const _errs3 = errors;
if(errors === _errs3){
if(Array.isArray(data1)){
var valid1 = true;
const len0 = data1.length;
for(let i0=0; i0<len0; i0++){
const _errs5 = errors;
if(!(validate143(data1[i0], {instancePath:instancePath+"/messages/" + i0,parentData:data1,parentDataProperty:i0,rootData,dynamicAnchors}))){
vErrors = vErrors === null ? validate143.errors : vErrors.concat(validate143.errors);
errors = vErrors.length;
}
var valid1 = _errs5 === errors;
if(!valid1){
break;
}
}
}
else {
validate142.errors = [{instancePath:instancePath+"/messages",schemaPath:"#/properties/messages/type",keyword:"type",params:{type: "array"},message:"must be array"}];
return false;
}
}
var valid0 = _errs3 === errors;
}
else {
var valid0 = true;
}
}
}
}
else {
validate142.errors = [{instancePath,schemaPath:"#/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
validate142.errors = vErrors;
return errors === 0;
}
validate142.evaluated = {"props":{"before":true,"messages":true},"dynamicProps":false,"dynamicItems":false};

export const history_error = validate147;
const schema176 = {"$schema":"https://json-schema.org/draft/2020-12/schema","additionalProperties":false,"properties":{"code":{"type":"string"},"message":{"type":"string"}},"required":["code","message"],"title":"ChatError","type":"object"};

function validate147(data, {instancePath="", parentData, parentDataProperty, rootData=data, dynamicAnchors={}}={}){
let vErrors = null;
let errors = 0;
const evaluated0 = validate147.evaluated;
if(evaluated0.dynamicProps){
evaluated0.props = undefined;
}
if(evaluated0.dynamicItems){
evaluated0.items = undefined;
}
if(errors === 0){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing0;
if(((data.code === undefined) && (missing0 = "code")) || ((data.message === undefined) && (missing0 = "message"))){
validate147.errors = [{instancePath,schemaPath:"#/required",keyword:"required",params:{missingProperty: missing0},message:"must have required property '"+missing0+"'"}];
return false;
}
else {
const _errs1 = errors;
for(const key0 in data){
if(!((key0 === "code") || (key0 === "message"))){
validate147.errors = [{instancePath,schemaPath:"#/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key0},message:"must NOT have additional properties"}];
return false;
break;
}
}
if(_errs1 === errors){
if(data.code !== undefined){
const _errs2 = errors;
if(typeof data.code !== "string"){
validate147.errors = [{instancePath:instancePath+"/code",schemaPath:"#/properties/code/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs2 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.message !== undefined){
const _errs4 = errors;
if(typeof data.message !== "string"){
validate147.errors = [{instancePath:instancePath+"/message",schemaPath:"#/properties/message/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs4 === errors;
}
else {
var valid0 = true;
}
}
}
}
}
else {
validate147.errors = [{instancePath,schemaPath:"#/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
validate147.errors = vErrors;
return errors === 0;
}
validate147.evaluated = {"props":true,"dynamicProps":false,"dynamicItems":false};

export const search_args = validate148;
const schema177 = {"$schema":"https://json-schema.org/draft/2020-12/schema","additionalProperties":false,"properties":{"before":{"type":["string","null"]},"conversation":{"type":"string"},"limit":{"format":"uint16","maximum":65535,"minimum":0,"type":"integer"},"text":{"type":"string"}},"required":["conversation","text","limit"],"title":"ChatSearchArgs","type":"object"};

function validate148(data, {instancePath="", parentData, parentDataProperty, rootData=data, dynamicAnchors={}}={}){
let vErrors = null;
let errors = 0;
const evaluated0 = validate148.evaluated;
if(evaluated0.dynamicProps){
evaluated0.props = undefined;
}
if(evaluated0.dynamicItems){
evaluated0.items = undefined;
}
if(errors === 0){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing0;
if((((data.conversation === undefined) && (missing0 = "conversation")) || ((data.text === undefined) && (missing0 = "text"))) || ((data.limit === undefined) && (missing0 = "limit"))){
validate148.errors = [{instancePath,schemaPath:"#/required",keyword:"required",params:{missingProperty: missing0},message:"must have required property '"+missing0+"'"}];
return false;
}
else {
const _errs1 = errors;
for(const key0 in data){
if(!((((key0 === "before") || (key0 === "conversation")) || (key0 === "limit")) || (key0 === "text"))){
validate148.errors = [{instancePath,schemaPath:"#/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key0},message:"must NOT have additional properties"}];
return false;
break;
}
}
if(_errs1 === errors){
if(data.before !== undefined){
let data0 = data.before;
const _errs2 = errors;
if((typeof data0 !== "string") && (data0 !== null)){
validate148.errors = [{instancePath:instancePath+"/before",schemaPath:"#/properties/before/type",keyword:"type",params:{type: schema177.properties.before.type},message:"must be string,null"}];
return false;
}
var valid0 = _errs2 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.conversation !== undefined){
const _errs4 = errors;
if(typeof data.conversation !== "string"){
validate148.errors = [{instancePath:instancePath+"/conversation",schemaPath:"#/properties/conversation/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs4 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.limit !== undefined){
let data2 = data.limit;
const _errs6 = errors;
if(!(((typeof data2 == "number") && (!(data2 % 1) && !isNaN(data2))) && (isFinite(data2)))){
validate148.errors = [{instancePath:instancePath+"/limit",schemaPath:"#/properties/limit/type",keyword:"type",params:{type: "integer"},message:"must be integer"}];
return false;
}
if(errors === _errs6){
if((typeof data2 == "number") && (isFinite(data2))){
if(data2 > 65535 || isNaN(data2)){
validate148.errors = [{instancePath:instancePath+"/limit",schemaPath:"#/properties/limit/maximum",keyword:"maximum",params:{comparison: "<=", limit: 65535},message:"must be <= 65535"}];
return false;
}
else {
if(data2 < 0 || isNaN(data2)){
validate148.errors = [{instancePath:instancePath+"/limit",schemaPath:"#/properties/limit/minimum",keyword:"minimum",params:{comparison: ">=", limit: 0},message:"must be >= 0"}];
return false;
}
}
}
}
var valid0 = _errs6 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.text !== undefined){
const _errs8 = errors;
if(typeof data.text !== "string"){
validate148.errors = [{instancePath:instancePath+"/text",schemaPath:"#/properties/text/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs8 === errors;
}
else {
var valid0 = true;
}
}
}
}
}
}
}
else {
validate148.errors = [{instancePath,schemaPath:"#/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
validate148.errors = vErrors;
return errors === 0;
}
validate148.evaluated = {"props":true,"dynamicProps":false,"dynamicItems":false};

export const search_output = validate149;
const schema178 = {"$defs":{"ActionResult":{"properties":{"artifacts":{"items":{"$ref":"#/$defs/Artifact"},"type":"array"},"details":{"items":{"type":"string"},"type":"array"},"id":{"type":"string"},"messageId":{"default":null,"type":["string","null"]},"outputBase64":{"description":"Exact signed bytes, base64 encoded; views decode only for display.","type":["string","null"]},"state":{"type":"string"},"stderr":{"type":"boolean"}},"required":["id","state","stderr","details","artifacts"],"type":"object"},"Artifact":{"properties":{"name":{"type":"string"},"url":{"type":"string"}},"required":["name","url"],"type":"object"},"Delivery":{"enum":["local_accepted","delivered"],"type":"string"},"Message":{"properties":{"body":{"type":"string"},"conversationId":{"type":"string"},"delivery":{"anyOf":[{"$ref":"#/$defs/Delivery"},{"type":"null"}],"description":"Delivered is an authenticated recipient acknowledgement, never a read receipt."},"id":{"type":"string"},"memberId":{"type":["string","null"]},"mine":{"type":"boolean"},"nickname":{"type":"string"},"operationId":{"default":null,"type":["string","null"]},"result":{"anyOf":[{"$ref":"#/$defs/ActionResult"},{"type":"null"}],"default":null},"timestamp":{"format":"uint64","minimum":0,"type":"integer"}},"required":["id","conversationId","nickname","body","timestamp","mine"],"type":"object"}},"$schema":"https://json-schema.org/draft/2020-12/schema","properties":{"before":{"type":["string","null"]},"messages":{"items":{"$ref":"#/$defs/Message"},"type":"array"}},"required":["messages"],"title":"HistoryPage","type":"object"};
const schema179 = {"properties":{"body":{"type":"string"},"conversationId":{"type":"string"},"delivery":{"anyOf":[{"$ref":"#/$defs/Delivery"},{"type":"null"}],"description":"Delivered is an authenticated recipient acknowledgement, never a read receipt."},"id":{"type":"string"},"memberId":{"type":["string","null"]},"mine":{"type":"boolean"},"nickname":{"type":"string"},"operationId":{"default":null,"type":["string","null"]},"result":{"anyOf":[{"$ref":"#/$defs/ActionResult"},{"type":"null"}],"default":null},"timestamp":{"format":"uint64","minimum":0,"type":"integer"}},"required":["id","conversationId","nickname","body","timestamp","mine"],"type":"object"};
const schema180 = {"enum":["local_accepted","delivered"],"type":"string"};
const schema181 = {"properties":{"artifacts":{"items":{"$ref":"#/$defs/Artifact"},"type":"array"},"details":{"items":{"type":"string"},"type":"array"},"id":{"type":"string"},"messageId":{"default":null,"type":["string","null"]},"outputBase64":{"description":"Exact signed bytes, base64 encoded; views decode only for display.","type":["string","null"]},"state":{"type":"string"},"stderr":{"type":"boolean"}},"required":["id","state","stderr","details","artifacts"],"type":"object"};
const schema182 = {"properties":{"name":{"type":"string"},"url":{"type":"string"}},"required":["name","url"],"type":"object"};

function validate151(data, {instancePath="", parentData, parentDataProperty, rootData=data, dynamicAnchors={}}={}){
let vErrors = null;
let errors = 0;
const evaluated0 = validate151.evaluated;
if(evaluated0.dynamicProps){
evaluated0.props = undefined;
}
if(evaluated0.dynamicItems){
evaluated0.items = undefined;
}
if(errors === 0){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing0;
if((((((data.id === undefined) && (missing0 = "id")) || ((data.state === undefined) && (missing0 = "state"))) || ((data.stderr === undefined) && (missing0 = "stderr"))) || ((data.details === undefined) && (missing0 = "details"))) || ((data.artifacts === undefined) && (missing0 = "artifacts"))){
validate151.errors = [{instancePath,schemaPath:"#/required",keyword:"required",params:{missingProperty: missing0},message:"must have required property '"+missing0+"'"}];
return false;
}
else {
if(data.artifacts !== undefined){
let data0 = data.artifacts;
const _errs1 = errors;
if(errors === _errs1){
if(Array.isArray(data0)){
var valid1 = true;
const len0 = data0.length;
for(let i0=0; i0<len0; i0++){
let data1 = data0[i0];
const _errs3 = errors;
const _errs4 = errors;
if(errors === _errs4){
if(data1 && typeof data1 == "object" && !Array.isArray(data1)){
let missing1;
if(((data1.name === undefined) && (missing1 = "name")) || ((data1.url === undefined) && (missing1 = "url"))){
validate151.errors = [{instancePath:instancePath+"/artifacts/" + i0,schemaPath:"#/$defs/Artifact/required",keyword:"required",params:{missingProperty: missing1},message:"must have required property '"+missing1+"'"}];
return false;
}
else {
if(data1.name !== undefined){
const _errs6 = errors;
if(typeof data1.name !== "string"){
validate151.errors = [{instancePath:instancePath+"/artifacts/" + i0+"/name",schemaPath:"#/$defs/Artifact/properties/name/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid3 = _errs6 === errors;
}
else {
var valid3 = true;
}
if(valid3){
if(data1.url !== undefined){
const _errs8 = errors;
if(typeof data1.url !== "string"){
validate151.errors = [{instancePath:instancePath+"/artifacts/" + i0+"/url",schemaPath:"#/$defs/Artifact/properties/url/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid3 = _errs8 === errors;
}
else {
var valid3 = true;
}
}
}
}
else {
validate151.errors = [{instancePath:instancePath+"/artifacts/" + i0,schemaPath:"#/$defs/Artifact/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
var valid1 = _errs3 === errors;
if(!valid1){
break;
}
}
}
else {
validate151.errors = [{instancePath:instancePath+"/artifacts",schemaPath:"#/properties/artifacts/type",keyword:"type",params:{type: "array"},message:"must be array"}];
return false;
}
}
var valid0 = _errs1 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.details !== undefined){
let data4 = data.details;
const _errs10 = errors;
if(errors === _errs10){
if(Array.isArray(data4)){
var valid4 = true;
const len1 = data4.length;
for(let i1=0; i1<len1; i1++){
const _errs12 = errors;
if(typeof data4[i1] !== "string"){
validate151.errors = [{instancePath:instancePath+"/details/" + i1,schemaPath:"#/properties/details/items/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid4 = _errs12 === errors;
if(!valid4){
break;
}
}
}
else {
validate151.errors = [{instancePath:instancePath+"/details",schemaPath:"#/properties/details/type",keyword:"type",params:{type: "array"},message:"must be array"}];
return false;
}
}
var valid0 = _errs10 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.id !== undefined){
const _errs14 = errors;
if(typeof data.id !== "string"){
validate151.errors = [{instancePath:instancePath+"/id",schemaPath:"#/properties/id/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs14 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.messageId !== undefined){
let data7 = data.messageId;
const _errs16 = errors;
if((typeof data7 !== "string") && (data7 !== null)){
validate151.errors = [{instancePath:instancePath+"/messageId",schemaPath:"#/properties/messageId/type",keyword:"type",params:{type: schema181.properties.messageId.type},message:"must be string,null"}];
return false;
}
var valid0 = _errs16 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.outputBase64 !== undefined){
let data8 = data.outputBase64;
const _errs18 = errors;
if((typeof data8 !== "string") && (data8 !== null)){
validate151.errors = [{instancePath:instancePath+"/outputBase64",schemaPath:"#/properties/outputBase64/type",keyword:"type",params:{type: schema181.properties.outputBase64.type},message:"must be string,null"}];
return false;
}
var valid0 = _errs18 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.state !== undefined){
const _errs20 = errors;
if(typeof data.state !== "string"){
validate151.errors = [{instancePath:instancePath+"/state",schemaPath:"#/properties/state/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs20 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.stderr !== undefined){
const _errs22 = errors;
if(typeof data.stderr !== "boolean"){
validate151.errors = [{instancePath:instancePath+"/stderr",schemaPath:"#/properties/stderr/type",keyword:"type",params:{type: "boolean"},message:"must be boolean"}];
return false;
}
var valid0 = _errs22 === errors;
}
else {
var valid0 = true;
}
}
}
}
}
}
}
}
}
else {
validate151.errors = [{instancePath,schemaPath:"#/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
validate151.errors = vErrors;
return errors === 0;
}
validate151.evaluated = {"props":{"artifacts":true,"details":true,"id":true,"messageId":true,"outputBase64":true,"state":true,"stderr":true},"dynamicProps":false,"dynamicItems":false};


function validate150(data, {instancePath="", parentData, parentDataProperty, rootData=data, dynamicAnchors={}}={}){
let vErrors = null;
let errors = 0;
const evaluated0 = validate150.evaluated;
if(evaluated0.dynamicProps){
evaluated0.props = undefined;
}
if(evaluated0.dynamicItems){
evaluated0.items = undefined;
}
if(errors === 0){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing0;
if(((((((data.id === undefined) && (missing0 = "id")) || ((data.conversationId === undefined) && (missing0 = "conversationId"))) || ((data.nickname === undefined) && (missing0 = "nickname"))) || ((data.body === undefined) && (missing0 = "body"))) || ((data.timestamp === undefined) && (missing0 = "timestamp"))) || ((data.mine === undefined) && (missing0 = "mine"))){
validate150.errors = [{instancePath,schemaPath:"#/required",keyword:"required",params:{missingProperty: missing0},message:"must have required property '"+missing0+"'"}];
return false;
}
else {
if(data.body !== undefined){
const _errs1 = errors;
if(typeof data.body !== "string"){
validate150.errors = [{instancePath:instancePath+"/body",schemaPath:"#/properties/body/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs1 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.conversationId !== undefined){
const _errs3 = errors;
if(typeof data.conversationId !== "string"){
validate150.errors = [{instancePath:instancePath+"/conversationId",schemaPath:"#/properties/conversationId/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs3 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.delivery !== undefined){
let data2 = data.delivery;
const _errs5 = errors;
const _errs6 = errors;
let valid1 = false;
const _errs7 = errors;
if(typeof data2 !== "string"){
const err0 = {instancePath:instancePath+"/delivery",schemaPath:"#/$defs/Delivery/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err0];
}
else {
vErrors.push(err0);
}
errors++;
}
if(!((data2 === "local_accepted") || (data2 === "delivered"))){
const err1 = {instancePath:instancePath+"/delivery",schemaPath:"#/$defs/Delivery/enum",keyword:"enum",params:{allowedValues: schema180.enum},message:"must be equal to one of the allowed values"};
if(vErrors === null){
vErrors = [err1];
}
else {
vErrors.push(err1);
}
errors++;
}
var _valid0 = _errs7 === errors;
valid1 = valid1 || _valid0;
const _errs10 = errors;
if(data2 !== null){
const err2 = {instancePath:instancePath+"/delivery",schemaPath:"#/properties/delivery/anyOf/1/type",keyword:"type",params:{type: "null"},message:"must be null"};
if(vErrors === null){
vErrors = [err2];
}
else {
vErrors.push(err2);
}
errors++;
}
var _valid0 = _errs10 === errors;
valid1 = valid1 || _valid0;
if(!valid1){
const err3 = {instancePath:instancePath+"/delivery",schemaPath:"#/properties/delivery/anyOf",keyword:"anyOf",params:{},message:"must match a schema in anyOf"};
if(vErrors === null){
vErrors = [err3];
}
else {
vErrors.push(err3);
}
errors++;
validate150.errors = vErrors;
return false;
}
else {
errors = _errs6;
if(vErrors !== null){
if(_errs6){
vErrors.length = _errs6;
}
else {
vErrors = null;
}
}
}
var valid0 = _errs5 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.id !== undefined){
const _errs12 = errors;
if(typeof data.id !== "string"){
validate150.errors = [{instancePath:instancePath+"/id",schemaPath:"#/properties/id/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs12 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.memberId !== undefined){
let data4 = data.memberId;
const _errs14 = errors;
if((typeof data4 !== "string") && (data4 !== null)){
validate150.errors = [{instancePath:instancePath+"/memberId",schemaPath:"#/properties/memberId/type",keyword:"type",params:{type: schema179.properties.memberId.type},message:"must be string,null"}];
return false;
}
var valid0 = _errs14 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.mine !== undefined){
const _errs16 = errors;
if(typeof data.mine !== "boolean"){
validate150.errors = [{instancePath:instancePath+"/mine",schemaPath:"#/properties/mine/type",keyword:"type",params:{type: "boolean"},message:"must be boolean"}];
return false;
}
var valid0 = _errs16 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.nickname !== undefined){
const _errs18 = errors;
if(typeof data.nickname !== "string"){
validate150.errors = [{instancePath:instancePath+"/nickname",schemaPath:"#/properties/nickname/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs18 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.operationId !== undefined){
let data7 = data.operationId;
const _errs20 = errors;
if((typeof data7 !== "string") && (data7 !== null)){
validate150.errors = [{instancePath:instancePath+"/operationId",schemaPath:"#/properties/operationId/type",keyword:"type",params:{type: schema179.properties.operationId.type},message:"must be string,null"}];
return false;
}
var valid0 = _errs20 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.result !== undefined){
let data8 = data.result;
const _errs22 = errors;
const _errs23 = errors;
let valid3 = false;
const _errs24 = errors;
if(!(validate151(data8, {instancePath:instancePath+"/result",parentData:data,parentDataProperty:"result",rootData,dynamicAnchors}))){
vErrors = vErrors === null ? validate151.errors : vErrors.concat(validate151.errors);
errors = vErrors.length;
}
var _valid1 = _errs24 === errors;
valid3 = valid3 || _valid1;
if(_valid1){
var props0 = {};
props0.artifacts = true;
props0.details = true;
props0.id = true;
props0.messageId = true;
props0.outputBase64 = true;
props0.state = true;
props0.stderr = true;
}
const _errs25 = errors;
if(data8 !== null){
const err4 = {instancePath:instancePath+"/result",schemaPath:"#/properties/result/anyOf/1/type",keyword:"type",params:{type: "null"},message:"must be null"};
if(vErrors === null){
vErrors = [err4];
}
else {
vErrors.push(err4);
}
errors++;
}
var _valid1 = _errs25 === errors;
valid3 = valid3 || _valid1;
if(!valid3){
const err5 = {instancePath:instancePath+"/result",schemaPath:"#/properties/result/anyOf",keyword:"anyOf",params:{},message:"must match a schema in anyOf"};
if(vErrors === null){
vErrors = [err5];
}
else {
vErrors.push(err5);
}
errors++;
validate150.errors = vErrors;
return false;
}
else {
errors = _errs23;
if(vErrors !== null){
if(_errs23){
vErrors.length = _errs23;
}
else {
vErrors = null;
}
}
}
var valid0 = _errs22 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.timestamp !== undefined){
let data9 = data.timestamp;
const _errs27 = errors;
if(!(((typeof data9 == "number") && (!(data9 % 1) && !isNaN(data9))) && (isFinite(data9)))){
validate150.errors = [{instancePath:instancePath+"/timestamp",schemaPath:"#/properties/timestamp/type",keyword:"type",params:{type: "integer"},message:"must be integer"}];
return false;
}
if(errors === _errs27){
if((typeof data9 == "number") && (isFinite(data9))){
if(data9 < 0 || isNaN(data9)){
validate150.errors = [{instancePath:instancePath+"/timestamp",schemaPath:"#/properties/timestamp/minimum",keyword:"minimum",params:{comparison: ">=", limit: 0},message:"must be >= 0"}];
return false;
}
}
}
var valid0 = _errs27 === errors;
}
else {
var valid0 = true;
}
}
}
}
}
}
}
}
}
}
}
}
else {
validate150.errors = [{instancePath,schemaPath:"#/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
validate150.errors = vErrors;
return errors === 0;
}
validate150.evaluated = {"props":{"body":true,"conversationId":true,"delivery":true,"id":true,"memberId":true,"mine":true,"nickname":true,"operationId":true,"result":true,"timestamp":true},"dynamicProps":false,"dynamicItems":false};


function validate149(data, {instancePath="", parentData, parentDataProperty, rootData=data, dynamicAnchors={}}={}){
let vErrors = null;
let errors = 0;
const evaluated0 = validate149.evaluated;
if(evaluated0.dynamicProps){
evaluated0.props = undefined;
}
if(evaluated0.dynamicItems){
evaluated0.items = undefined;
}
if(errors === 0){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing0;
if((data.messages === undefined) && (missing0 = "messages")){
validate149.errors = [{instancePath,schemaPath:"#/required",keyword:"required",params:{missingProperty: missing0},message:"must have required property '"+missing0+"'"}];
return false;
}
else {
if(data.before !== undefined){
let data0 = data.before;
const _errs1 = errors;
if((typeof data0 !== "string") && (data0 !== null)){
validate149.errors = [{instancePath:instancePath+"/before",schemaPath:"#/properties/before/type",keyword:"type",params:{type: schema178.properties.before.type},message:"must be string,null"}];
return false;
}
var valid0 = _errs1 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.messages !== undefined){
let data1 = data.messages;
const _errs3 = errors;
if(errors === _errs3){
if(Array.isArray(data1)){
var valid1 = true;
const len0 = data1.length;
for(let i0=0; i0<len0; i0++){
const _errs5 = errors;
if(!(validate150(data1[i0], {instancePath:instancePath+"/messages/" + i0,parentData:data1,parentDataProperty:i0,rootData,dynamicAnchors}))){
vErrors = vErrors === null ? validate150.errors : vErrors.concat(validate150.errors);
errors = vErrors.length;
}
var valid1 = _errs5 === errors;
if(!valid1){
break;
}
}
}
else {
validate149.errors = [{instancePath:instancePath+"/messages",schemaPath:"#/properties/messages/type",keyword:"type",params:{type: "array"},message:"must be array"}];
return false;
}
}
var valid0 = _errs3 === errors;
}
else {
var valid0 = true;
}
}
}
}
else {
validate149.errors = [{instancePath,schemaPath:"#/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
validate149.errors = vErrors;
return errors === 0;
}
validate149.evaluated = {"props":{"before":true,"messages":true},"dynamicProps":false,"dynamicItems":false};

export const search_error = validate154;
const schema183 = {"$schema":"https://json-schema.org/draft/2020-12/schema","additionalProperties":false,"properties":{"code":{"type":"string"},"message":{"type":"string"}},"required":["code","message"],"title":"ChatError","type":"object"};

function validate154(data, {instancePath="", parentData, parentDataProperty, rootData=data, dynamicAnchors={}}={}){
let vErrors = null;
let errors = 0;
const evaluated0 = validate154.evaluated;
if(evaluated0.dynamicProps){
evaluated0.props = undefined;
}
if(evaluated0.dynamicItems){
evaluated0.items = undefined;
}
if(errors === 0){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing0;
if(((data.code === undefined) && (missing0 = "code")) || ((data.message === undefined) && (missing0 = "message"))){
validate154.errors = [{instancePath,schemaPath:"#/required",keyword:"required",params:{missingProperty: missing0},message:"must have required property '"+missing0+"'"}];
return false;
}
else {
const _errs1 = errors;
for(const key0 in data){
if(!((key0 === "code") || (key0 === "message"))){
validate154.errors = [{instancePath,schemaPath:"#/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key0},message:"must NOT have additional properties"}];
return false;
break;
}
}
if(_errs1 === errors){
if(data.code !== undefined){
const _errs2 = errors;
if(typeof data.code !== "string"){
validate154.errors = [{instancePath:instancePath+"/code",schemaPath:"#/properties/code/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs2 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.message !== undefined){
const _errs4 = errors;
if(typeof data.message !== "string"){
validate154.errors = [{instancePath:instancePath+"/message",schemaPath:"#/properties/message/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs4 === errors;
}
else {
var valid0 = true;
}
}
}
}
}
else {
validate154.errors = [{instancePath,schemaPath:"#/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
validate154.errors = vErrors;
return errors === 0;
}
validate154.evaluated = {"props":true,"dynamicProps":false,"dynamicItems":false};

export const submit_args = validate155;
const schema184 = {"$schema":"https://json-schema.org/draft/2020-12/schema","additionalProperties":false,"properties":{"conversation":{"type":["string","null"]},"text":{"type":"string"}},"required":["text"],"title":"ChatSubmitArgs","type":"object"};

function validate155(data, {instancePath="", parentData, parentDataProperty, rootData=data, dynamicAnchors={}}={}){
let vErrors = null;
let errors = 0;
const evaluated0 = validate155.evaluated;
if(evaluated0.dynamicProps){
evaluated0.props = undefined;
}
if(evaluated0.dynamicItems){
evaluated0.items = undefined;
}
if(errors === 0){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing0;
if((data.text === undefined) && (missing0 = "text")){
validate155.errors = [{instancePath,schemaPath:"#/required",keyword:"required",params:{missingProperty: missing0},message:"must have required property '"+missing0+"'"}];
return false;
}
else {
const _errs1 = errors;
for(const key0 in data){
if(!((key0 === "conversation") || (key0 === "text"))){
validate155.errors = [{instancePath,schemaPath:"#/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key0},message:"must NOT have additional properties"}];
return false;
break;
}
}
if(_errs1 === errors){
if(data.conversation !== undefined){
let data0 = data.conversation;
const _errs2 = errors;
if((typeof data0 !== "string") && (data0 !== null)){
validate155.errors = [{instancePath:instancePath+"/conversation",schemaPath:"#/properties/conversation/type",keyword:"type",params:{type: schema184.properties.conversation.type},message:"must be string,null"}];
return false;
}
var valid0 = _errs2 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.text !== undefined){
const _errs4 = errors;
if(typeof data.text !== "string"){
validate155.errors = [{instancePath:instancePath+"/text",schemaPath:"#/properties/text/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs4 === errors;
}
else {
var valid0 = true;
}
}
}
}
}
else {
validate155.errors = [{instancePath,schemaPath:"#/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
validate155.errors = vErrors;
return errors === 0;
}
validate155.evaluated = {"props":true,"dynamicProps":false,"dynamicItems":false};

export const submit_output = validate156;
const schema185 = {"$defs":{"CommandOutput":{"oneOf":[{"properties":{"commands":{"items":{"$ref":"#/$defs/CommandSpec"},"type":"array"},"kind":{"const":"help","type":"string"}},"required":["kind","commands"],"type":"object"},{"properties":{"channels":{"items":{"$ref":"#/$defs/DirectoryEntry"},"type":"array"},"kind":{"const":"directory","type":"string"}},"required":["kind","channels"],"type":"object"},{"properties":{"channel":{"type":"string"},"expires":{"format":"uint64","minimum":0,"type":"integer"},"kind":{"const":"invitation","type":"string"},"link":{"type":"string"},"localOnly":{"default":false,"type":"boolean"}},"required":["kind","channel","link","expires"],"type":"object"},{"properties":{"kind":{"const":"text","type":"string"},"text":{"type":"string"},"title":{"type":"string"}},"required":["kind","title","text"],"type":"object"},{"properties":{"kind":{"const":"status","type":"string"},"text":{"type":"string"}},"required":["kind","text"],"type":"object"},{"properties":{"conversation":{"type":"string"},"kind":{"const":"close","type":"string"}},"required":["kind","conversation"],"type":"object"}]},"CommandSpec":{"properties":{"available":{"type":"boolean"},"capability":{"type":["string","null"]},"description":{"type":"string"},"name":{"type":"string"},"scope":{"type":"string"},"usage":{"type":"string"}},"required":["name","usage","description","scope","available"],"type":"object"},"DirectoryEntry":{"properties":{"conversation":{"type":["string","null"]},"joined":{"type":"boolean"},"name":{"type":"string"}},"required":["name","joined"],"type":"object"}},"$schema":"https://json-schema.org/draft/2020-12/schema","oneOf":[{"additionalProperties":false,"properties":{"conversation":{"type":["string","null"]},"kind":{"const":"applied","type":"string"},"notice":{"type":["string","null"]}},"required":["kind"],"type":"object"},{"additionalProperties":false,"properties":{"conversation":{"type":["string","null"]},"kind":{"const":"output","type":"string"},"output":{"$ref":"#/$defs/CommandOutput"}},"required":["kind","output"],"type":"object"}],"title":"SubmitOutcome"};
const schema186 = {"oneOf":[{"properties":{"commands":{"items":{"$ref":"#/$defs/CommandSpec"},"type":"array"},"kind":{"const":"help","type":"string"}},"required":["kind","commands"],"type":"object"},{"properties":{"channels":{"items":{"$ref":"#/$defs/DirectoryEntry"},"type":"array"},"kind":{"const":"directory","type":"string"}},"required":["kind","channels"],"type":"object"},{"properties":{"channel":{"type":"string"},"expires":{"format":"uint64","minimum":0,"type":"integer"},"kind":{"const":"invitation","type":"string"},"link":{"type":"string"},"localOnly":{"default":false,"type":"boolean"}},"required":["kind","channel","link","expires"],"type":"object"},{"properties":{"kind":{"const":"text","type":"string"},"text":{"type":"string"},"title":{"type":"string"}},"required":["kind","title","text"],"type":"object"},{"properties":{"kind":{"const":"status","type":"string"},"text":{"type":"string"}},"required":["kind","text"],"type":"object"},{"properties":{"conversation":{"type":"string"},"kind":{"const":"close","type":"string"}},"required":["kind","conversation"],"type":"object"}]};
const schema187 = {"properties":{"available":{"type":"boolean"},"capability":{"type":["string","null"]},"description":{"type":"string"},"name":{"type":"string"},"scope":{"type":"string"},"usage":{"type":"string"}},"required":["name","usage","description","scope","available"],"type":"object"};
const schema188 = {"properties":{"conversation":{"type":["string","null"]},"joined":{"type":"boolean"},"name":{"type":"string"}},"required":["name","joined"],"type":"object"};

function validate157(data, {instancePath="", parentData, parentDataProperty, rootData=data, dynamicAnchors={}}={}){
let vErrors = null;
let errors = 0;
const evaluated0 = validate157.evaluated;
if(evaluated0.dynamicProps){
evaluated0.props = undefined;
}
if(evaluated0.dynamicItems){
evaluated0.items = undefined;
}
const _errs0 = errors;
let valid0 = false;
let passing0 = null;
const _errs1 = errors;
if(errors === _errs1){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing0;
if(((data.kind === undefined) && (missing0 = "kind")) || ((data.commands === undefined) && (missing0 = "commands"))){
const err0 = {instancePath,schemaPath:"#/oneOf/0/required",keyword:"required",params:{missingProperty: missing0},message:"must have required property '"+missing0+"'"};
if(vErrors === null){
vErrors = [err0];
}
else {
vErrors.push(err0);
}
errors++;
}
else {
if(data.commands !== undefined){
let data0 = data.commands;
const _errs3 = errors;
if(errors === _errs3){
if(Array.isArray(data0)){
var valid2 = true;
const len0 = data0.length;
for(let i0=0; i0<len0; i0++){
let data1 = data0[i0];
const _errs5 = errors;
const _errs6 = errors;
if(errors === _errs6){
if(data1 && typeof data1 == "object" && !Array.isArray(data1)){
let missing1;
if((((((data1.name === undefined) && (missing1 = "name")) || ((data1.usage === undefined) && (missing1 = "usage"))) || ((data1.description === undefined) && (missing1 = "description"))) || ((data1.scope === undefined) && (missing1 = "scope"))) || ((data1.available === undefined) && (missing1 = "available"))){
const err1 = {instancePath:instancePath+"/commands/" + i0,schemaPath:"#/$defs/CommandSpec/required",keyword:"required",params:{missingProperty: missing1},message:"must have required property '"+missing1+"'"};
if(vErrors === null){
vErrors = [err1];
}
else {
vErrors.push(err1);
}
errors++;
}
else {
if(data1.available !== undefined){
const _errs8 = errors;
if(typeof data1.available !== "boolean"){
const err2 = {instancePath:instancePath+"/commands/" + i0+"/available",schemaPath:"#/$defs/CommandSpec/properties/available/type",keyword:"type",params:{type: "boolean"},message:"must be boolean"};
if(vErrors === null){
vErrors = [err2];
}
else {
vErrors.push(err2);
}
errors++;
}
var valid4 = _errs8 === errors;
}
else {
var valid4 = true;
}
if(valid4){
if(data1.capability !== undefined){
let data3 = data1.capability;
const _errs10 = errors;
if((typeof data3 !== "string") && (data3 !== null)){
const err3 = {instancePath:instancePath+"/commands/" + i0+"/capability",schemaPath:"#/$defs/CommandSpec/properties/capability/type",keyword:"type",params:{type: schema187.properties.capability.type},message:"must be string,null"};
if(vErrors === null){
vErrors = [err3];
}
else {
vErrors.push(err3);
}
errors++;
}
var valid4 = _errs10 === errors;
}
else {
var valid4 = true;
}
if(valid4){
if(data1.description !== undefined){
const _errs12 = errors;
if(typeof data1.description !== "string"){
const err4 = {instancePath:instancePath+"/commands/" + i0+"/description",schemaPath:"#/$defs/CommandSpec/properties/description/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err4];
}
else {
vErrors.push(err4);
}
errors++;
}
var valid4 = _errs12 === errors;
}
else {
var valid4 = true;
}
if(valid4){
if(data1.name !== undefined){
const _errs14 = errors;
if(typeof data1.name !== "string"){
const err5 = {instancePath:instancePath+"/commands/" + i0+"/name",schemaPath:"#/$defs/CommandSpec/properties/name/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err5];
}
else {
vErrors.push(err5);
}
errors++;
}
var valid4 = _errs14 === errors;
}
else {
var valid4 = true;
}
if(valid4){
if(data1.scope !== undefined){
const _errs16 = errors;
if(typeof data1.scope !== "string"){
const err6 = {instancePath:instancePath+"/commands/" + i0+"/scope",schemaPath:"#/$defs/CommandSpec/properties/scope/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err6];
}
else {
vErrors.push(err6);
}
errors++;
}
var valid4 = _errs16 === errors;
}
else {
var valid4 = true;
}
if(valid4){
if(data1.usage !== undefined){
const _errs18 = errors;
if(typeof data1.usage !== "string"){
const err7 = {instancePath:instancePath+"/commands/" + i0+"/usage",schemaPath:"#/$defs/CommandSpec/properties/usage/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err7];
}
else {
vErrors.push(err7);
}
errors++;
}
var valid4 = _errs18 === errors;
}
else {
var valid4 = true;
}
}
}
}
}
}
}
}
else {
const err8 = {instancePath:instancePath+"/commands/" + i0,schemaPath:"#/$defs/CommandSpec/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err8];
}
else {
vErrors.push(err8);
}
errors++;
}
}
var valid2 = _errs5 === errors;
if(!valid2){
break;
}
}
}
else {
const err9 = {instancePath:instancePath+"/commands",schemaPath:"#/oneOf/0/properties/commands/type",keyword:"type",params:{type: "array"},message:"must be array"};
if(vErrors === null){
vErrors = [err9];
}
else {
vErrors.push(err9);
}
errors++;
}
}
var valid1 = _errs3 === errors;
}
else {
var valid1 = true;
}
if(valid1){
if(data.kind !== undefined){
let data8 = data.kind;
const _errs20 = errors;
if(typeof data8 !== "string"){
const err10 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/0/properties/kind/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err10];
}
else {
vErrors.push(err10);
}
errors++;
}
if("help" !== data8){
const err11 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/0/properties/kind/const",keyword:"const",params:{allowedValue: "help"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err11];
}
else {
vErrors.push(err11);
}
errors++;
}
var valid1 = _errs20 === errors;
}
else {
var valid1 = true;
}
}
}
}
else {
const err12 = {instancePath,schemaPath:"#/oneOf/0/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err12];
}
else {
vErrors.push(err12);
}
errors++;
}
}
var _valid0 = _errs1 === errors;
if(_valid0){
valid0 = true;
passing0 = 0;
var props0 = {};
props0.commands = true;
props0.kind = true;
}
const _errs22 = errors;
if(errors === _errs22){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing2;
if(((data.kind === undefined) && (missing2 = "kind")) || ((data.channels === undefined) && (missing2 = "channels"))){
const err13 = {instancePath,schemaPath:"#/oneOf/1/required",keyword:"required",params:{missingProperty: missing2},message:"must have required property '"+missing2+"'"};
if(vErrors === null){
vErrors = [err13];
}
else {
vErrors.push(err13);
}
errors++;
}
else {
if(data.channels !== undefined){
let data9 = data.channels;
const _errs24 = errors;
if(errors === _errs24){
if(Array.isArray(data9)){
var valid6 = true;
const len1 = data9.length;
for(let i1=0; i1<len1; i1++){
let data10 = data9[i1];
const _errs26 = errors;
const _errs27 = errors;
if(errors === _errs27){
if(data10 && typeof data10 == "object" && !Array.isArray(data10)){
let missing3;
if(((data10.name === undefined) && (missing3 = "name")) || ((data10.joined === undefined) && (missing3 = "joined"))){
const err14 = {instancePath:instancePath+"/channels/" + i1,schemaPath:"#/$defs/DirectoryEntry/required",keyword:"required",params:{missingProperty: missing3},message:"must have required property '"+missing3+"'"};
if(vErrors === null){
vErrors = [err14];
}
else {
vErrors.push(err14);
}
errors++;
}
else {
if(data10.conversation !== undefined){
let data11 = data10.conversation;
const _errs29 = errors;
if((typeof data11 !== "string") && (data11 !== null)){
const err15 = {instancePath:instancePath+"/channels/" + i1+"/conversation",schemaPath:"#/$defs/DirectoryEntry/properties/conversation/type",keyword:"type",params:{type: schema188.properties.conversation.type},message:"must be string,null"};
if(vErrors === null){
vErrors = [err15];
}
else {
vErrors.push(err15);
}
errors++;
}
var valid8 = _errs29 === errors;
}
else {
var valid8 = true;
}
if(valid8){
if(data10.joined !== undefined){
const _errs31 = errors;
if(typeof data10.joined !== "boolean"){
const err16 = {instancePath:instancePath+"/channels/" + i1+"/joined",schemaPath:"#/$defs/DirectoryEntry/properties/joined/type",keyword:"type",params:{type: "boolean"},message:"must be boolean"};
if(vErrors === null){
vErrors = [err16];
}
else {
vErrors.push(err16);
}
errors++;
}
var valid8 = _errs31 === errors;
}
else {
var valid8 = true;
}
if(valid8){
if(data10.name !== undefined){
const _errs33 = errors;
if(typeof data10.name !== "string"){
const err17 = {instancePath:instancePath+"/channels/" + i1+"/name",schemaPath:"#/$defs/DirectoryEntry/properties/name/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err17];
}
else {
vErrors.push(err17);
}
errors++;
}
var valid8 = _errs33 === errors;
}
else {
var valid8 = true;
}
}
}
}
}
else {
const err18 = {instancePath:instancePath+"/channels/" + i1,schemaPath:"#/$defs/DirectoryEntry/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err18];
}
else {
vErrors.push(err18);
}
errors++;
}
}
var valid6 = _errs26 === errors;
if(!valid6){
break;
}
}
}
else {
const err19 = {instancePath:instancePath+"/channels",schemaPath:"#/oneOf/1/properties/channels/type",keyword:"type",params:{type: "array"},message:"must be array"};
if(vErrors === null){
vErrors = [err19];
}
else {
vErrors.push(err19);
}
errors++;
}
}
var valid5 = _errs24 === errors;
}
else {
var valid5 = true;
}
if(valid5){
if(data.kind !== undefined){
let data14 = data.kind;
const _errs35 = errors;
if(typeof data14 !== "string"){
const err20 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/1/properties/kind/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err20];
}
else {
vErrors.push(err20);
}
errors++;
}
if("directory" !== data14){
const err21 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/1/properties/kind/const",keyword:"const",params:{allowedValue: "directory"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err21];
}
else {
vErrors.push(err21);
}
errors++;
}
var valid5 = _errs35 === errors;
}
else {
var valid5 = true;
}
}
}
}
else {
const err22 = {instancePath,schemaPath:"#/oneOf/1/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err22];
}
else {
vErrors.push(err22);
}
errors++;
}
}
var _valid0 = _errs22 === errors;
if(_valid0 && valid0){
valid0 = false;
passing0 = [passing0, 1];
}
else {
if(_valid0){
valid0 = true;
passing0 = 1;
if(props0 !== true){
props0 = props0 || {};
props0.channels = true;
props0.kind = true;
}
}
const _errs37 = errors;
if(errors === _errs37){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing4;
if(((((data.kind === undefined) && (missing4 = "kind")) || ((data.channel === undefined) && (missing4 = "channel"))) || ((data.link === undefined) && (missing4 = "link"))) || ((data.expires === undefined) && (missing4 = "expires"))){
const err23 = {instancePath,schemaPath:"#/oneOf/2/required",keyword:"required",params:{missingProperty: missing4},message:"must have required property '"+missing4+"'"};
if(vErrors === null){
vErrors = [err23];
}
else {
vErrors.push(err23);
}
errors++;
}
else {
if(data.channel !== undefined){
const _errs39 = errors;
if(typeof data.channel !== "string"){
const err24 = {instancePath:instancePath+"/channel",schemaPath:"#/oneOf/2/properties/channel/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err24];
}
else {
vErrors.push(err24);
}
errors++;
}
var valid9 = _errs39 === errors;
}
else {
var valid9 = true;
}
if(valid9){
if(data.expires !== undefined){
let data16 = data.expires;
const _errs41 = errors;
if(!(((typeof data16 == "number") && (!(data16 % 1) && !isNaN(data16))) && (isFinite(data16)))){
const err25 = {instancePath:instancePath+"/expires",schemaPath:"#/oneOf/2/properties/expires/type",keyword:"type",params:{type: "integer"},message:"must be integer"};
if(vErrors === null){
vErrors = [err25];
}
else {
vErrors.push(err25);
}
errors++;
}
if(errors === _errs41){
if((typeof data16 == "number") && (isFinite(data16))){
if(data16 < 0 || isNaN(data16)){
const err26 = {instancePath:instancePath+"/expires",schemaPath:"#/oneOf/2/properties/expires/minimum",keyword:"minimum",params:{comparison: ">=", limit: 0},message:"must be >= 0"};
if(vErrors === null){
vErrors = [err26];
}
else {
vErrors.push(err26);
}
errors++;
}
}
}
var valid9 = _errs41 === errors;
}
else {
var valid9 = true;
}
if(valid9){
if(data.kind !== undefined){
let data17 = data.kind;
const _errs43 = errors;
if(typeof data17 !== "string"){
const err27 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/2/properties/kind/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err27];
}
else {
vErrors.push(err27);
}
errors++;
}
if("invitation" !== data17){
const err28 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/2/properties/kind/const",keyword:"const",params:{allowedValue: "invitation"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err28];
}
else {
vErrors.push(err28);
}
errors++;
}
var valid9 = _errs43 === errors;
}
else {
var valid9 = true;
}
if(valid9){
if(data.link !== undefined){
const _errs45 = errors;
if(typeof data.link !== "string"){
const err29 = {instancePath:instancePath+"/link",schemaPath:"#/oneOf/2/properties/link/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err29];
}
else {
vErrors.push(err29);
}
errors++;
}
var valid9 = _errs45 === errors;
}
else {
var valid9 = true;
}
if(valid9){
if(data.localOnly !== undefined){
const _errs47 = errors;
if(typeof data.localOnly !== "boolean"){
const err30 = {instancePath:instancePath+"/localOnly",schemaPath:"#/oneOf/2/properties/localOnly/type",keyword:"type",params:{type: "boolean"},message:"must be boolean"};
if(vErrors === null){
vErrors = [err30];
}
else {
vErrors.push(err30);
}
errors++;
}
var valid9 = _errs47 === errors;
}
else {
var valid9 = true;
}
}
}
}
}
}
}
else {
const err31 = {instancePath,schemaPath:"#/oneOf/2/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err31];
}
else {
vErrors.push(err31);
}
errors++;
}
}
var _valid0 = _errs37 === errors;
if(_valid0 && valid0){
valid0 = false;
passing0 = [passing0, 2];
}
else {
if(_valid0){
valid0 = true;
passing0 = 2;
if(props0 !== true){
props0 = props0 || {};
props0.channel = true;
props0.expires = true;
props0.kind = true;
props0.link = true;
props0.localOnly = true;
}
}
const _errs49 = errors;
if(errors === _errs49){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing5;
if((((data.kind === undefined) && (missing5 = "kind")) || ((data.title === undefined) && (missing5 = "title"))) || ((data.text === undefined) && (missing5 = "text"))){
const err32 = {instancePath,schemaPath:"#/oneOf/3/required",keyword:"required",params:{missingProperty: missing5},message:"must have required property '"+missing5+"'"};
if(vErrors === null){
vErrors = [err32];
}
else {
vErrors.push(err32);
}
errors++;
}
else {
if(data.kind !== undefined){
let data20 = data.kind;
const _errs51 = errors;
if(typeof data20 !== "string"){
const err33 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/3/properties/kind/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err33];
}
else {
vErrors.push(err33);
}
errors++;
}
if("text" !== data20){
const err34 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/3/properties/kind/const",keyword:"const",params:{allowedValue: "text"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err34];
}
else {
vErrors.push(err34);
}
errors++;
}
var valid10 = _errs51 === errors;
}
else {
var valid10 = true;
}
if(valid10){
if(data.text !== undefined){
const _errs53 = errors;
if(typeof data.text !== "string"){
const err35 = {instancePath:instancePath+"/text",schemaPath:"#/oneOf/3/properties/text/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err35];
}
else {
vErrors.push(err35);
}
errors++;
}
var valid10 = _errs53 === errors;
}
else {
var valid10 = true;
}
if(valid10){
if(data.title !== undefined){
const _errs55 = errors;
if(typeof data.title !== "string"){
const err36 = {instancePath:instancePath+"/title",schemaPath:"#/oneOf/3/properties/title/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err36];
}
else {
vErrors.push(err36);
}
errors++;
}
var valid10 = _errs55 === errors;
}
else {
var valid10 = true;
}
}
}
}
}
else {
const err37 = {instancePath,schemaPath:"#/oneOf/3/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err37];
}
else {
vErrors.push(err37);
}
errors++;
}
}
var _valid0 = _errs49 === errors;
if(_valid0 && valid0){
valid0 = false;
passing0 = [passing0, 3];
}
else {
if(_valid0){
valid0 = true;
passing0 = 3;
if(props0 !== true){
props0 = props0 || {};
props0.kind = true;
props0.text = true;
props0.title = true;
}
}
const _errs57 = errors;
if(errors === _errs57){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing6;
if(((data.kind === undefined) && (missing6 = "kind")) || ((data.text === undefined) && (missing6 = "text"))){
const err38 = {instancePath,schemaPath:"#/oneOf/4/required",keyword:"required",params:{missingProperty: missing6},message:"must have required property '"+missing6+"'"};
if(vErrors === null){
vErrors = [err38];
}
else {
vErrors.push(err38);
}
errors++;
}
else {
if(data.kind !== undefined){
let data23 = data.kind;
const _errs59 = errors;
if(typeof data23 !== "string"){
const err39 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/4/properties/kind/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err39];
}
else {
vErrors.push(err39);
}
errors++;
}
if("status" !== data23){
const err40 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/4/properties/kind/const",keyword:"const",params:{allowedValue: "status"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err40];
}
else {
vErrors.push(err40);
}
errors++;
}
var valid11 = _errs59 === errors;
}
else {
var valid11 = true;
}
if(valid11){
if(data.text !== undefined){
const _errs61 = errors;
if(typeof data.text !== "string"){
const err41 = {instancePath:instancePath+"/text",schemaPath:"#/oneOf/4/properties/text/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err41];
}
else {
vErrors.push(err41);
}
errors++;
}
var valid11 = _errs61 === errors;
}
else {
var valid11 = true;
}
}
}
}
else {
const err42 = {instancePath,schemaPath:"#/oneOf/4/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err42];
}
else {
vErrors.push(err42);
}
errors++;
}
}
var _valid0 = _errs57 === errors;
if(_valid0 && valid0){
valid0 = false;
passing0 = [passing0, 4];
}
else {
if(_valid0){
valid0 = true;
passing0 = 4;
if(props0 !== true){
props0 = props0 || {};
props0.kind = true;
props0.text = true;
}
}
const _errs63 = errors;
if(errors === _errs63){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing7;
if(((data.kind === undefined) && (missing7 = "kind")) || ((data.conversation === undefined) && (missing7 = "conversation"))){
const err43 = {instancePath,schemaPath:"#/oneOf/5/required",keyword:"required",params:{missingProperty: missing7},message:"must have required property '"+missing7+"'"};
if(vErrors === null){
vErrors = [err43];
}
else {
vErrors.push(err43);
}
errors++;
}
else {
if(data.conversation !== undefined){
const _errs65 = errors;
if(typeof data.conversation !== "string"){
const err44 = {instancePath:instancePath+"/conversation",schemaPath:"#/oneOf/5/properties/conversation/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err44];
}
else {
vErrors.push(err44);
}
errors++;
}
var valid12 = _errs65 === errors;
}
else {
var valid12 = true;
}
if(valid12){
if(data.kind !== undefined){
let data26 = data.kind;
const _errs67 = errors;
if(typeof data26 !== "string"){
const err45 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/5/properties/kind/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err45];
}
else {
vErrors.push(err45);
}
errors++;
}
if("close" !== data26){
const err46 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/5/properties/kind/const",keyword:"const",params:{allowedValue: "close"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err46];
}
else {
vErrors.push(err46);
}
errors++;
}
var valid12 = _errs67 === errors;
}
else {
var valid12 = true;
}
}
}
}
else {
const err47 = {instancePath,schemaPath:"#/oneOf/5/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err47];
}
else {
vErrors.push(err47);
}
errors++;
}
}
var _valid0 = _errs63 === errors;
if(_valid0 && valid0){
valid0 = false;
passing0 = [passing0, 5];
}
else {
if(_valid0){
valid0 = true;
passing0 = 5;
if(props0 !== true){
props0 = props0 || {};
props0.conversation = true;
props0.kind = true;
}
}
}
}
}
}
}
if(!valid0){
const err48 = {instancePath,schemaPath:"#/oneOf",keyword:"oneOf",params:{passingSchemas: passing0},message:"must match exactly one schema in oneOf"};
if(vErrors === null){
vErrors = [err48];
}
else {
vErrors.push(err48);
}
errors++;
validate157.errors = vErrors;
return false;
}
else {
errors = _errs0;
if(vErrors !== null){
if(_errs0){
vErrors.length = _errs0;
}
else {
vErrors = null;
}
}
}
validate157.errors = vErrors;
evaluated0.props = props0;
return errors === 0;
}
validate157.evaluated = {"dynamicProps":true,"dynamicItems":false};


function validate156(data, {instancePath="", parentData, parentDataProperty, rootData=data, dynamicAnchors={}}={}){
let vErrors = null;
let errors = 0;
const evaluated0 = validate156.evaluated;
if(evaluated0.dynamicProps){
evaluated0.props = undefined;
}
if(evaluated0.dynamicItems){
evaluated0.items = undefined;
}
const _errs0 = errors;
let valid0 = false;
let passing0 = null;
const _errs1 = errors;
if(errors === _errs1){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing0;
if((data.kind === undefined) && (missing0 = "kind")){
const err0 = {instancePath,schemaPath:"#/oneOf/0/required",keyword:"required",params:{missingProperty: missing0},message:"must have required property '"+missing0+"'"};
if(vErrors === null){
vErrors = [err0];
}
else {
vErrors.push(err0);
}
errors++;
}
else {
const _errs3 = errors;
for(const key0 in data){
if(!(((key0 === "conversation") || (key0 === "kind")) || (key0 === "notice"))){
const err1 = {instancePath,schemaPath:"#/oneOf/0/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key0},message:"must NOT have additional properties"};
if(vErrors === null){
vErrors = [err1];
}
else {
vErrors.push(err1);
}
errors++;
break;
}
}
if(_errs3 === errors){
if(data.conversation !== undefined){
let data0 = data.conversation;
const _errs4 = errors;
if((typeof data0 !== "string") && (data0 !== null)){
const err2 = {instancePath:instancePath+"/conversation",schemaPath:"#/oneOf/0/properties/conversation/type",keyword:"type",params:{type: schema185.oneOf[0].properties.conversation.type},message:"must be string,null"};
if(vErrors === null){
vErrors = [err2];
}
else {
vErrors.push(err2);
}
errors++;
}
var valid1 = _errs4 === errors;
}
else {
var valid1 = true;
}
if(valid1){
if(data.kind !== undefined){
let data1 = data.kind;
const _errs6 = errors;
if(typeof data1 !== "string"){
const err3 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/0/properties/kind/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err3];
}
else {
vErrors.push(err3);
}
errors++;
}
if("applied" !== data1){
const err4 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/0/properties/kind/const",keyword:"const",params:{allowedValue: "applied"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err4];
}
else {
vErrors.push(err4);
}
errors++;
}
var valid1 = _errs6 === errors;
}
else {
var valid1 = true;
}
if(valid1){
if(data.notice !== undefined){
let data2 = data.notice;
const _errs8 = errors;
if((typeof data2 !== "string") && (data2 !== null)){
const err5 = {instancePath:instancePath+"/notice",schemaPath:"#/oneOf/0/properties/notice/type",keyword:"type",params:{type: schema185.oneOf[0].properties.notice.type},message:"must be string,null"};
if(vErrors === null){
vErrors = [err5];
}
else {
vErrors.push(err5);
}
errors++;
}
var valid1 = _errs8 === errors;
}
else {
var valid1 = true;
}
}
}
}
}
}
else {
const err6 = {instancePath,schemaPath:"#/oneOf/0/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err6];
}
else {
vErrors.push(err6);
}
errors++;
}
}
var _valid0 = _errs1 === errors;
if(_valid0){
valid0 = true;
passing0 = 0;
var props0 = true;
}
const _errs10 = errors;
if(errors === _errs10){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing1;
if(((data.kind === undefined) && (missing1 = "kind")) || ((data.output === undefined) && (missing1 = "output"))){
const err7 = {instancePath,schemaPath:"#/oneOf/1/required",keyword:"required",params:{missingProperty: missing1},message:"must have required property '"+missing1+"'"};
if(vErrors === null){
vErrors = [err7];
}
else {
vErrors.push(err7);
}
errors++;
}
else {
const _errs12 = errors;
for(const key1 in data){
if(!(((key1 === "conversation") || (key1 === "kind")) || (key1 === "output"))){
const err8 = {instancePath,schemaPath:"#/oneOf/1/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key1},message:"must NOT have additional properties"};
if(vErrors === null){
vErrors = [err8];
}
else {
vErrors.push(err8);
}
errors++;
break;
}
}
if(_errs12 === errors){
if(data.conversation !== undefined){
let data3 = data.conversation;
const _errs13 = errors;
if((typeof data3 !== "string") && (data3 !== null)){
const err9 = {instancePath:instancePath+"/conversation",schemaPath:"#/oneOf/1/properties/conversation/type",keyword:"type",params:{type: schema185.oneOf[1].properties.conversation.type},message:"must be string,null"};
if(vErrors === null){
vErrors = [err9];
}
else {
vErrors.push(err9);
}
errors++;
}
var valid2 = _errs13 === errors;
}
else {
var valid2 = true;
}
if(valid2){
if(data.kind !== undefined){
let data4 = data.kind;
const _errs15 = errors;
if(typeof data4 !== "string"){
const err10 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/1/properties/kind/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err10];
}
else {
vErrors.push(err10);
}
errors++;
}
if("output" !== data4){
const err11 = {instancePath:instancePath+"/kind",schemaPath:"#/oneOf/1/properties/kind/const",keyword:"const",params:{allowedValue: "output"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err11];
}
else {
vErrors.push(err11);
}
errors++;
}
var valid2 = _errs15 === errors;
}
else {
var valid2 = true;
}
if(valid2){
if(data.output !== undefined){
const _errs17 = errors;
if(!(validate157(data.output, {instancePath:instancePath+"/output",parentData:data,parentDataProperty:"output",rootData,dynamicAnchors}))){
vErrors = vErrors === null ? validate157.errors : vErrors.concat(validate157.errors);
errors = vErrors.length;
}
var valid2 = _errs17 === errors;
}
else {
var valid2 = true;
}
}
}
}
}
}
else {
const err12 = {instancePath,schemaPath:"#/oneOf/1/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err12];
}
else {
vErrors.push(err12);
}
errors++;
}
}
var _valid0 = _errs10 === errors;
if(_valid0 && valid0){
valid0 = false;
passing0 = [passing0, 1];
}
else {
if(_valid0){
valid0 = true;
passing0 = 1;
if(props0 !== true){
props0 = true;
}
}
}
if(!valid0){
const err13 = {instancePath,schemaPath:"#/oneOf",keyword:"oneOf",params:{passingSchemas: passing0},message:"must match exactly one schema in oneOf"};
if(vErrors === null){
vErrors = [err13];
}
else {
vErrors.push(err13);
}
errors++;
validate156.errors = vErrors;
return false;
}
else {
errors = _errs0;
if(vErrors !== null){
if(_errs0){
vErrors.length = _errs0;
}
else {
vErrors = null;
}
}
}
validate156.errors = vErrors;
evaluated0.props = props0;
return errors === 0;
}
validate156.evaluated = {"dynamicProps":true,"dynamicItems":false};

export const submit_error = validate159;
const schema189 = {"$schema":"https://json-schema.org/draft/2020-12/schema","additionalProperties":false,"properties":{"code":{"type":"string"},"message":{"type":"string"}},"required":["code","message"],"title":"ChatError","type":"object"};

function validate159(data, {instancePath="", parentData, parentDataProperty, rootData=data, dynamicAnchors={}}={}){
let vErrors = null;
let errors = 0;
const evaluated0 = validate159.evaluated;
if(evaluated0.dynamicProps){
evaluated0.props = undefined;
}
if(evaluated0.dynamicItems){
evaluated0.items = undefined;
}
if(errors === 0){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing0;
if(((data.code === undefined) && (missing0 = "code")) || ((data.message === undefined) && (missing0 = "message"))){
validate159.errors = [{instancePath,schemaPath:"#/required",keyword:"required",params:{missingProperty: missing0},message:"must have required property '"+missing0+"'"}];
return false;
}
else {
const _errs1 = errors;
for(const key0 in data){
if(!((key0 === "code") || (key0 === "message"))){
validate159.errors = [{instancePath,schemaPath:"#/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key0},message:"must NOT have additional properties"}];
return false;
break;
}
}
if(_errs1 === errors){
if(data.code !== undefined){
const _errs2 = errors;
if(typeof data.code !== "string"){
validate159.errors = [{instancePath:instancePath+"/code",schemaPath:"#/properties/code/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs2 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.message !== undefined){
const _errs4 = errors;
if(typeof data.message !== "string"){
validate159.errors = [{instancePath:instancePath+"/message",schemaPath:"#/properties/message/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs4 === errors;
}
else {
var valid0 = true;
}
}
}
}
}
else {
validate159.errors = [{instancePath,schemaPath:"#/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
validate159.errors = vErrors;
return errors === 0;
}
validate159.evaluated = {"props":true,"dynamicProps":false,"dynamicItems":false};

export const complete_args = validate160;
const schema190 = {"$schema":"https://json-schema.org/draft/2020-12/schema","additionalProperties":false,"properties":{"conversation":{"type":["string","null"]},"text":{"type":"string"}},"required":["text"],"title":"ChatCompleteArgs","type":"object"};

function validate160(data, {instancePath="", parentData, parentDataProperty, rootData=data, dynamicAnchors={}}={}){
let vErrors = null;
let errors = 0;
const evaluated0 = validate160.evaluated;
if(evaluated0.dynamicProps){
evaluated0.props = undefined;
}
if(evaluated0.dynamicItems){
evaluated0.items = undefined;
}
if(errors === 0){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing0;
if((data.text === undefined) && (missing0 = "text")){
validate160.errors = [{instancePath,schemaPath:"#/required",keyword:"required",params:{missingProperty: missing0},message:"must have required property '"+missing0+"'"}];
return false;
}
else {
const _errs1 = errors;
for(const key0 in data){
if(!((key0 === "conversation") || (key0 === "text"))){
validate160.errors = [{instancePath,schemaPath:"#/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key0},message:"must NOT have additional properties"}];
return false;
break;
}
}
if(_errs1 === errors){
if(data.conversation !== undefined){
let data0 = data.conversation;
const _errs2 = errors;
if((typeof data0 !== "string") && (data0 !== null)){
validate160.errors = [{instancePath:instancePath+"/conversation",schemaPath:"#/properties/conversation/type",keyword:"type",params:{type: schema190.properties.conversation.type},message:"must be string,null"}];
return false;
}
var valid0 = _errs2 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.text !== undefined){
const _errs4 = errors;
if(typeof data.text !== "string"){
validate160.errors = [{instancePath:instancePath+"/text",schemaPath:"#/properties/text/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs4 === errors;
}
else {
var valid0 = true;
}
}
}
}
}
else {
validate160.errors = [{instancePath,schemaPath:"#/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
validate160.errors = vErrors;
return errors === 0;
}
validate160.evaluated = {"props":true,"dynamicProps":false,"dynamicItems":false};

export const complete_output = validate161;
const schema191 = {"$defs":{"Completion":{"properties":{"description":{"type":"string"},"text":{"type":"string"}},"required":["text","description"],"type":"object"}},"$schema":"https://json-schema.org/draft/2020-12/schema","items":{"$ref":"#/$defs/Completion"},"title":"Array_of_Completion","type":"array"};
const schema192 = {"properties":{"description":{"type":"string"},"text":{"type":"string"}},"required":["text","description"],"type":"object"};

function validate161(data, {instancePath="", parentData, parentDataProperty, rootData=data, dynamicAnchors={}}={}){
let vErrors = null;
let errors = 0;
const evaluated0 = validate161.evaluated;
if(evaluated0.dynamicProps){
evaluated0.props = undefined;
}
if(evaluated0.dynamicItems){
evaluated0.items = undefined;
}
if(errors === 0){
if(Array.isArray(data)){
var valid0 = true;
const len0 = data.length;
for(let i0=0; i0<len0; i0++){
let data0 = data[i0];
const _errs1 = errors;
const _errs2 = errors;
if(errors === _errs2){
if(data0 && typeof data0 == "object" && !Array.isArray(data0)){
let missing0;
if(((data0.text === undefined) && (missing0 = "text")) || ((data0.description === undefined) && (missing0 = "description"))){
validate161.errors = [{instancePath:instancePath+"/" + i0,schemaPath:"#/$defs/Completion/required",keyword:"required",params:{missingProperty: missing0},message:"must have required property '"+missing0+"'"}];
return false;
}
else {
if(data0.description !== undefined){
const _errs4 = errors;
if(typeof data0.description !== "string"){
validate161.errors = [{instancePath:instancePath+"/" + i0+"/description",schemaPath:"#/$defs/Completion/properties/description/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid2 = _errs4 === errors;
}
else {
var valid2 = true;
}
if(valid2){
if(data0.text !== undefined){
const _errs6 = errors;
if(typeof data0.text !== "string"){
validate161.errors = [{instancePath:instancePath+"/" + i0+"/text",schemaPath:"#/$defs/Completion/properties/text/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid2 = _errs6 === errors;
}
else {
var valid2 = true;
}
}
}
}
else {
validate161.errors = [{instancePath:instancePath+"/" + i0,schemaPath:"#/$defs/Completion/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
var valid0 = _errs1 === errors;
if(!valid0){
break;
}
}
}
else {
validate161.errors = [{instancePath,schemaPath:"#/type",keyword:"type",params:{type: "array"},message:"must be array"}];
return false;
}
}
validate161.errors = vErrors;
return errors === 0;
}
validate161.evaluated = {"items":true,"dynamicProps":false,"dynamicItems":false};

export const complete_error = validate162;
const schema193 = {"$schema":"https://json-schema.org/draft/2020-12/schema","additionalProperties":false,"properties":{"code":{"type":"string"},"message":{"type":"string"}},"required":["code","message"],"title":"ChatError","type":"object"};

function validate162(data, {instancePath="", parentData, parentDataProperty, rootData=data, dynamicAnchors={}}={}){
let vErrors = null;
let errors = 0;
const evaluated0 = validate162.evaluated;
if(evaluated0.dynamicProps){
evaluated0.props = undefined;
}
if(evaluated0.dynamicItems){
evaluated0.items = undefined;
}
if(errors === 0){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing0;
if(((data.code === undefined) && (missing0 = "code")) || ((data.message === undefined) && (missing0 = "message"))){
validate162.errors = [{instancePath,schemaPath:"#/required",keyword:"required",params:{missingProperty: missing0},message:"must have required property '"+missing0+"'"}];
return false;
}
else {
const _errs1 = errors;
for(const key0 in data){
if(!((key0 === "code") || (key0 === "message"))){
validate162.errors = [{instancePath,schemaPath:"#/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key0},message:"must NOT have additional properties"}];
return false;
break;
}
}
if(_errs1 === errors){
if(data.code !== undefined){
const _errs2 = errors;
if(typeof data.code !== "string"){
validate162.errors = [{instancePath:instancePath+"/code",schemaPath:"#/properties/code/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs2 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.message !== undefined){
const _errs4 = errors;
if(typeof data.message !== "string"){
validate162.errors = [{instancePath:instancePath+"/message",schemaPath:"#/properties/message/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs4 === errors;
}
else {
var valid0 = true;
}
}
}
}
}
else {
validate162.errors = [{instancePath,schemaPath:"#/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
validate162.errors = vErrors;
return errors === 0;
}
validate162.evaluated = {"props":true,"dynamicProps":false,"dynamicItems":false};

export const mark_read_args = validate163;
const schema194 = {"$schema":"https://json-schema.org/draft/2020-12/schema","additionalProperties":false,"properties":{"conversation":{"type":"string"},"message_id":{"type":"string"}},"required":["conversation","message_id"],"title":"ChatMarkReadArgs","type":"object"};

function validate163(data, {instancePath="", parentData, parentDataProperty, rootData=data, dynamicAnchors={}}={}){
let vErrors = null;
let errors = 0;
const evaluated0 = validate163.evaluated;
if(evaluated0.dynamicProps){
evaluated0.props = undefined;
}
if(evaluated0.dynamicItems){
evaluated0.items = undefined;
}
if(errors === 0){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing0;
if(((data.conversation === undefined) && (missing0 = "conversation")) || ((data.message_id === undefined) && (missing0 = "message_id"))){
validate163.errors = [{instancePath,schemaPath:"#/required",keyword:"required",params:{missingProperty: missing0},message:"must have required property '"+missing0+"'"}];
return false;
}
else {
const _errs1 = errors;
for(const key0 in data){
if(!((key0 === "conversation") || (key0 === "message_id"))){
validate163.errors = [{instancePath,schemaPath:"#/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key0},message:"must NOT have additional properties"}];
return false;
break;
}
}
if(_errs1 === errors){
if(data.conversation !== undefined){
const _errs2 = errors;
if(typeof data.conversation !== "string"){
validate163.errors = [{instancePath:instancePath+"/conversation",schemaPath:"#/properties/conversation/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs2 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.message_id !== undefined){
const _errs4 = errors;
if(typeof data.message_id !== "string"){
validate163.errors = [{instancePath:instancePath+"/message_id",schemaPath:"#/properties/message_id/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs4 === errors;
}
else {
var valid0 = true;
}
}
}
}
}
else {
validate163.errors = [{instancePath,schemaPath:"#/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
validate163.errors = vErrors;
return errors === 0;
}
validate163.evaluated = {"props":true,"dynamicProps":false,"dynamicItems":false};

export const mark_read_output = validate164;
const schema195 = {"$schema":"https://json-schema.org/draft/2020-12/schema","additionalProperties":false,"properties":{"conversation":{"type":["string","null"]},"notice":{"type":["string","null"]}},"title":"Applied","type":"object"};

function validate164(data, {instancePath="", parentData, parentDataProperty, rootData=data, dynamicAnchors={}}={}){
let vErrors = null;
let errors = 0;
const evaluated0 = validate164.evaluated;
if(evaluated0.dynamicProps){
evaluated0.props = undefined;
}
if(evaluated0.dynamicItems){
evaluated0.items = undefined;
}
if(errors === 0){
if(data && typeof data == "object" && !Array.isArray(data)){
const _errs1 = errors;
for(const key0 in data){
if(!((key0 === "conversation") || (key0 === "notice"))){
validate164.errors = [{instancePath,schemaPath:"#/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key0},message:"must NOT have additional properties"}];
return false;
break;
}
}
if(_errs1 === errors){
if(data.conversation !== undefined){
let data0 = data.conversation;
const _errs2 = errors;
if((typeof data0 !== "string") && (data0 !== null)){
validate164.errors = [{instancePath:instancePath+"/conversation",schemaPath:"#/properties/conversation/type",keyword:"type",params:{type: schema195.properties.conversation.type},message:"must be string,null"}];
return false;
}
var valid0 = _errs2 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.notice !== undefined){
let data1 = data.notice;
const _errs4 = errors;
if((typeof data1 !== "string") && (data1 !== null)){
validate164.errors = [{instancePath:instancePath+"/notice",schemaPath:"#/properties/notice/type",keyword:"type",params:{type: schema195.properties.notice.type},message:"must be string,null"}];
return false;
}
var valid0 = _errs4 === errors;
}
else {
var valid0 = true;
}
}
}
}
else {
validate164.errors = [{instancePath,schemaPath:"#/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
validate164.errors = vErrors;
return errors === 0;
}
validate164.evaluated = {"props":true,"dynamicProps":false,"dynamicItems":false};

export const mark_read_error = validate165;
const schema196 = {"$schema":"https://json-schema.org/draft/2020-12/schema","additionalProperties":false,"properties":{"code":{"type":"string"},"message":{"type":"string"}},"required":["code","message"],"title":"ChatError","type":"object"};

function validate165(data, {instancePath="", parentData, parentDataProperty, rootData=data, dynamicAnchors={}}={}){
let vErrors = null;
let errors = 0;
const evaluated0 = validate165.evaluated;
if(evaluated0.dynamicProps){
evaluated0.props = undefined;
}
if(evaluated0.dynamicItems){
evaluated0.items = undefined;
}
if(errors === 0){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing0;
if(((data.code === undefined) && (missing0 = "code")) || ((data.message === undefined) && (missing0 = "message"))){
validate165.errors = [{instancePath,schemaPath:"#/required",keyword:"required",params:{missingProperty: missing0},message:"must have required property '"+missing0+"'"}];
return false;
}
else {
const _errs1 = errors;
for(const key0 in data){
if(!((key0 === "code") || (key0 === "message"))){
validate165.errors = [{instancePath,schemaPath:"#/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key0},message:"must NOT have additional properties"}];
return false;
break;
}
}
if(_errs1 === errors){
if(data.code !== undefined){
const _errs2 = errors;
if(typeof data.code !== "string"){
validate165.errors = [{instancePath:instancePath+"/code",schemaPath:"#/properties/code/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs2 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.message !== undefined){
const _errs4 = errors;
if(typeof data.message !== "string"){
validate165.errors = [{instancePath:instancePath+"/message",schemaPath:"#/properties/message/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs4 === errors;
}
else {
var valid0 = true;
}
}
}
}
}
else {
validate165.errors = [{instancePath,schemaPath:"#/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
validate165.errors = vErrors;
return errors === 0;
}
validate165.evaluated = {"props":true,"dynamicProps":false,"dynamicItems":false};

export const events_args = validate166;
const schema197 = {"$schema":"https://json-schema.org/draft/2020-12/schema","additionalProperties":false,"properties":{"after":{"type":"string"},"wait_ms":{"format":"uint16","maximum":65535,"minimum":0,"type":"integer"}},"required":["after","wait_ms"],"title":"ChatEventsArgs","type":"object"};

function validate166(data, {instancePath="", parentData, parentDataProperty, rootData=data, dynamicAnchors={}}={}){
let vErrors = null;
let errors = 0;
const evaluated0 = validate166.evaluated;
if(evaluated0.dynamicProps){
evaluated0.props = undefined;
}
if(evaluated0.dynamicItems){
evaluated0.items = undefined;
}
if(errors === 0){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing0;
if(((data.after === undefined) && (missing0 = "after")) || ((data.wait_ms === undefined) && (missing0 = "wait_ms"))){
validate166.errors = [{instancePath,schemaPath:"#/required",keyword:"required",params:{missingProperty: missing0},message:"must have required property '"+missing0+"'"}];
return false;
}
else {
const _errs1 = errors;
for(const key0 in data){
if(!((key0 === "after") || (key0 === "wait_ms"))){
validate166.errors = [{instancePath,schemaPath:"#/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key0},message:"must NOT have additional properties"}];
return false;
break;
}
}
if(_errs1 === errors){
if(data.after !== undefined){
const _errs2 = errors;
if(typeof data.after !== "string"){
validate166.errors = [{instancePath:instancePath+"/after",schemaPath:"#/properties/after/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs2 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.wait_ms !== undefined){
let data1 = data.wait_ms;
const _errs4 = errors;
if(!(((typeof data1 == "number") && (!(data1 % 1) && !isNaN(data1))) && (isFinite(data1)))){
validate166.errors = [{instancePath:instancePath+"/wait_ms",schemaPath:"#/properties/wait_ms/type",keyword:"type",params:{type: "integer"},message:"must be integer"}];
return false;
}
if(errors === _errs4){
if((typeof data1 == "number") && (isFinite(data1))){
if(data1 > 65535 || isNaN(data1)){
validate166.errors = [{instancePath:instancePath+"/wait_ms",schemaPath:"#/properties/wait_ms/maximum",keyword:"maximum",params:{comparison: "<=", limit: 65535},message:"must be <= 65535"}];
return false;
}
else {
if(data1 < 0 || isNaN(data1)){
validate166.errors = [{instancePath:instancePath+"/wait_ms",schemaPath:"#/properties/wait_ms/minimum",keyword:"minimum",params:{comparison: ">=", limit: 0},message:"must be >= 0"}];
return false;
}
}
}
}
var valid0 = _errs4 === errors;
}
else {
var valid0 = true;
}
}
}
}
}
else {
validate166.errors = [{instancePath,schemaPath:"#/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
validate166.errors = vErrors;
return errors === 0;
}
validate166.evaluated = {"props":true,"dynamicProps":false,"dynamicItems":false};

export const events_output = validate167;
const schema198 = {"$schema":"https://json-schema.org/draft/2020-12/schema","title":"string","type":"string"};

function validate167(data, {instancePath="", parentData, parentDataProperty, rootData=data, dynamicAnchors={}}={}){
let vErrors = null;
let errors = 0;
const evaluated0 = validate167.evaluated;
if(evaluated0.dynamicProps){
evaluated0.props = undefined;
}
if(evaluated0.dynamicItems){
evaluated0.items = undefined;
}
if(typeof data !== "string"){
validate167.errors = [{instancePath,schemaPath:"#/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
validate167.errors = vErrors;
return errors === 0;
}
validate167.evaluated = {"dynamicProps":false,"dynamicItems":false};

export const events_error = validate168;
const schema199 = {"$schema":"https://json-schema.org/draft/2020-12/schema","additionalProperties":false,"properties":{"code":{"type":"string"},"message":{"type":"string"}},"required":["code","message"],"title":"ChatError","type":"object"};

function validate168(data, {instancePath="", parentData, parentDataProperty, rootData=data, dynamicAnchors={}}={}){
let vErrors = null;
let errors = 0;
const evaluated0 = validate168.evaluated;
if(evaluated0.dynamicProps){
evaluated0.props = undefined;
}
if(evaluated0.dynamicItems){
evaluated0.items = undefined;
}
if(errors === 0){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing0;
if(((data.code === undefined) && (missing0 = "code")) || ((data.message === undefined) && (missing0 = "message"))){
validate168.errors = [{instancePath,schemaPath:"#/required",keyword:"required",params:{missingProperty: missing0},message:"must have required property '"+missing0+"'"}];
return false;
}
else {
const _errs1 = errors;
for(const key0 in data){
if(!((key0 === "code") || (key0 === "message"))){
validate168.errors = [{instancePath,schemaPath:"#/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key0},message:"must NOT have additional properties"}];
return false;
break;
}
}
if(_errs1 === errors){
if(data.code !== undefined){
const _errs2 = errors;
if(typeof data.code !== "string"){
validate168.errors = [{instancePath:instancePath+"/code",schemaPath:"#/properties/code/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs2 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.message !== undefined){
const _errs4 = errors;
if(typeof data.message !== "string"){
validate168.errors = [{instancePath:instancePath+"/message",schemaPath:"#/properties/message/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs4 === errors;
}
else {
var valid0 = true;
}
}
}
}
}
else {
validate168.errors = [{instancePath,schemaPath:"#/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
validate168.errors = vErrors;
return errors === 0;
}
validate168.evaluated = {"props":true,"dynamicProps":false,"dynamicItems":false};
