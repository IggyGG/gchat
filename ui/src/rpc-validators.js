// @ts-nocheck
// Generated from Rust JSON schemas. Do not edit.
"use strict";
export const identify_args = validate20;
const schema31 = {"$schema":"https://json-schema.org/draft/2020-12/schema","additionalProperties":false,"title":"ChatIdentifyArgs","type":"object"};

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
for(const key0 in data){
validate20.errors = [{instancePath,schemaPath:"#/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key0},message:"must NOT have additional properties"}];
return false;
break;
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

export const identify_output = validate21;
const schema32 = {"$schema":"https://json-schema.org/draft/2020-12/schema","properties":{"archiveExists":{"type":"boolean"},"bootId":{"type":"string"},"capabilities":{"items":{"type":"string"},"type":"array"},"id":{"type":"string"},"label":{"type":"string"},"locked":{"type":"boolean"},"profileExists":{"type":"boolean"},"protocolLocked":{"type":"boolean"},"safetyNumber":{"type":"string"}},"required":["id","label","bootId","locked","protocolLocked","profileExists","archiveExists","safetyNumber","capabilities"],"title":"InstanceInfo","type":"object"};

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
if(errors === 0){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing0;
if((((((((((data.id === undefined) && (missing0 = "id")) || ((data.label === undefined) && (missing0 = "label"))) || ((data.bootId === undefined) && (missing0 = "bootId"))) || ((data.locked === undefined) && (missing0 = "locked"))) || ((data.protocolLocked === undefined) && (missing0 = "protocolLocked"))) || ((data.profileExists === undefined) && (missing0 = "profileExists"))) || ((data.archiveExists === undefined) && (missing0 = "archiveExists"))) || ((data.safetyNumber === undefined) && (missing0 = "safetyNumber"))) || ((data.capabilities === undefined) && (missing0 = "capabilities"))){
validate21.errors = [{instancePath,schemaPath:"#/required",keyword:"required",params:{missingProperty: missing0},message:"must have required property '"+missing0+"'"}];
return false;
}
else {
if(data.archiveExists !== undefined){
const _errs1 = errors;
if(typeof data.archiveExists !== "boolean"){
validate21.errors = [{instancePath:instancePath+"/archiveExists",schemaPath:"#/properties/archiveExists/type",keyword:"type",params:{type: "boolean"},message:"must be boolean"}];
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
validate21.errors = [{instancePath:instancePath+"/bootId",schemaPath:"#/properties/bootId/type",keyword:"type",params:{type: "string"},message:"must be string"}];
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
validate21.errors = [{instancePath:instancePath+"/capabilities/" + i0,schemaPath:"#/properties/capabilities/items/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid1 = _errs7 === errors;
if(!valid1){
break;
}
}
}
else {
validate21.errors = [{instancePath:instancePath+"/capabilities",schemaPath:"#/properties/capabilities/type",keyword:"type",params:{type: "array"},message:"must be array"}];
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
validate21.errors = [{instancePath:instancePath+"/id",schemaPath:"#/properties/id/type",keyword:"type",params:{type: "string"},message:"must be string"}];
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
validate21.errors = [{instancePath:instancePath+"/label",schemaPath:"#/properties/label/type",keyword:"type",params:{type: "string"},message:"must be string"}];
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
validate21.errors = [{instancePath:instancePath+"/locked",schemaPath:"#/properties/locked/type",keyword:"type",params:{type: "boolean"},message:"must be boolean"}];
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
validate21.errors = [{instancePath:instancePath+"/profileExists",schemaPath:"#/properties/profileExists/type",keyword:"type",params:{type: "boolean"},message:"must be boolean"}];
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
validate21.errors = [{instancePath:instancePath+"/protocolLocked",schemaPath:"#/properties/protocolLocked/type",keyword:"type",params:{type: "boolean"},message:"must be boolean"}];
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
validate21.errors = [{instancePath:instancePath+"/safetyNumber",schemaPath:"#/properties/safetyNumber/type",keyword:"type",params:{type: "string"},message:"must be string"}];
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
validate21.errors = [{instancePath,schemaPath:"#/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
validate21.errors = vErrors;
return errors === 0;
}
validate21.evaluated = {"props":{"archiveExists":true,"bootId":true,"capabilities":true,"id":true,"label":true,"locked":true,"profileExists":true,"protocolLocked":true,"safetyNumber":true},"dynamicProps":false,"dynamicItems":false};

export const identify_error = validate22;
const schema33 = {"$schema":"https://json-schema.org/draft/2020-12/schema","additionalProperties":false,"properties":{"code":{"type":"string"},"message":{"type":"string"}},"required":["code","message"],"title":"ChatError","type":"object"};

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
if(errors === 0){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing0;
if(((data.code === undefined) && (missing0 = "code")) || ((data.message === undefined) && (missing0 = "message"))){
validate22.errors = [{instancePath,schemaPath:"#/required",keyword:"required",params:{missingProperty: missing0},message:"must have required property '"+missing0+"'"}];
return false;
}
else {
const _errs1 = errors;
for(const key0 in data){
if(!((key0 === "code") || (key0 === "message"))){
validate22.errors = [{instancePath,schemaPath:"#/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key0},message:"must NOT have additional properties"}];
return false;
break;
}
}
if(_errs1 === errors){
if(data.code !== undefined){
const _errs2 = errors;
if(typeof data.code !== "string"){
validate22.errors = [{instancePath:instancePath+"/code",schemaPath:"#/properties/code/type",keyword:"type",params:{type: "string"},message:"must be string"}];
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
validate22.errors = [{instancePath:instancePath+"/message",schemaPath:"#/properties/message/type",keyword:"type",params:{type: "string"},message:"must be string"}];
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
validate22.errors = [{instancePath,schemaPath:"#/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
validate22.errors = vErrors;
return errors === 0;
}
validate22.evaluated = {"props":true,"dynamicProps":false,"dynamicItems":false};

export const unlock_args = validate23;
const schema34 = {"$schema":"https://json-schema.org/draft/2020-12/schema","additionalProperties":false,"properties":{"create":{"type":"boolean"},"passphrase":{"type":"string"}},"required":["passphrase","create"],"title":"ChatUnlockArgs","type":"object"};

function validate23(data, {instancePath="", parentData, parentDataProperty, rootData=data, dynamicAnchors={}}={}){
let vErrors = null;
let errors = 0;
const evaluated0 = validate23.evaluated;
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
validate23.errors = [{instancePath,schemaPath:"#/required",keyword:"required",params:{missingProperty: missing0},message:"must have required property '"+missing0+"'"}];
return false;
}
else {
const _errs1 = errors;
for(const key0 in data){
if(!((key0 === "create") || (key0 === "passphrase"))){
validate23.errors = [{instancePath,schemaPath:"#/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key0},message:"must NOT have additional properties"}];
return false;
break;
}
}
if(_errs1 === errors){
if(data.create !== undefined){
const _errs2 = errors;
if(typeof data.create !== "boolean"){
validate23.errors = [{instancePath:instancePath+"/create",schemaPath:"#/properties/create/type",keyword:"type",params:{type: "boolean"},message:"must be boolean"}];
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
validate23.errors = [{instancePath:instancePath+"/passphrase",schemaPath:"#/properties/passphrase/type",keyword:"type",params:{type: "string"},message:"must be string"}];
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
validate23.errors = [{instancePath,schemaPath:"#/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
validate23.errors = vErrors;
return errors === 0;
}
validate23.evaluated = {"props":true,"dynamicProps":false,"dynamicItems":false};

export const unlock_output = validate24;
const schema35 = {"$defs":{"CommandSpec":{"properties":{"available":{"type":"boolean"},"capability":{"type":["string","null"]},"description":{"type":"string"},"name":{"type":"string"},"scope":{"type":"string"},"usage":{"type":"string"}},"required":["name","usage","description","scope","available"],"type":"object"},"Conversation":{"properties":{"active":{"type":"boolean"},"channelId":{"type":"string"},"commands":{"default":[],"items":{"$ref":"#/$defs/CommandSpec"},"type":"array"},"id":{"type":"string"},"inputLimitBytes":{"default":12000,"format":"uint","minimum":0,"type":"integer"},"kind":{"$ref":"#/$defs/ConversationKind"},"lastMessageId":{"type":["string","null"]},"members":{"items":{"$ref":"#/$defs/Member"},"type":"array"},"name":{"type":"string"},"owner":{"type":"boolean"},"provider":{"default":null,"type":["string","null"]},"topic":{"type":"string"},"unread":{"format":"uint32","minimum":0,"type":"integer"}},"required":["id","channelId","kind","name","topic","active","owner","members","unread"],"type":"object"},"ConversationKind":{"enum":["channel","query","archive"],"type":"string"},"InputHistoryEntry":{"properties":{"conversation":{"type":["string","null"]},"text":{"type":"string"}},"required":["text"],"type":"object"},"InstanceInfo":{"properties":{"archiveExists":{"type":"boolean"},"bootId":{"type":"string"},"capabilities":{"items":{"type":"string"},"type":"array"},"id":{"type":"string"},"label":{"type":"string"},"locked":{"type":"boolean"},"profileExists":{"type":"boolean"},"protocolLocked":{"type":"boolean"},"safetyNumber":{"type":"string"}},"required":["id","label","bootId","locked","protocolLocked","profileExists","archiveExists","safetyNumber","capabilities"],"type":"object"},"Member":{"properties":{"capabilities":{"default":[],"items":{"type":"string"},"type":"array"},"id":{"type":"string"},"isSelf":{"type":"boolean"},"nickname":{"type":"string"}},"required":["id","nickname","isSelf"],"type":"object"},"ProviderStatus":{"properties":{"code":{"type":"string"},"id":{"type":"string"},"message":{"type":"string"},"retryable":{"type":"boolean"}},"required":["id","code","message","retryable"],"type":"object"}},"$schema":"https://json-schema.org/draft/2020-12/schema","properties":{"commandHistory":{"items":{"type":"string"},"type":"array"},"conversations":{"items":{"$ref":"#/$defs/Conversation"},"type":"array"},"inputHistory":{"items":{"$ref":"#/$defs/InputHistoryEntry"},"type":"array"},"instance":{"$ref":"#/$defs/InstanceInfo"},"providerErrors":{"default":[],"items":{"$ref":"#/$defs/ProviderStatus"},"type":"array"},"revision":{"type":"string"}},"required":["instance","revision","conversations","commandHistory","inputHistory"],"title":"Snapshot","type":"object"};
const schema40 = {"properties":{"conversation":{"type":["string","null"]},"text":{"type":"string"}},"required":["text"],"type":"object"};
const schema41 = {"properties":{"archiveExists":{"type":"boolean"},"bootId":{"type":"string"},"capabilities":{"items":{"type":"string"},"type":"array"},"id":{"type":"string"},"label":{"type":"string"},"locked":{"type":"boolean"},"profileExists":{"type":"boolean"},"protocolLocked":{"type":"boolean"},"safetyNumber":{"type":"string"}},"required":["id","label","bootId","locked","protocolLocked","profileExists","archiveExists","safetyNumber","capabilities"],"type":"object"};
const schema42 = {"properties":{"code":{"type":"string"},"id":{"type":"string"},"message":{"type":"string"},"retryable":{"type":"boolean"}},"required":["id","code","message","retryable"],"type":"object"};
const schema36 = {"properties":{"active":{"type":"boolean"},"channelId":{"type":"string"},"commands":{"default":[],"items":{"$ref":"#/$defs/CommandSpec"},"type":"array"},"id":{"type":"string"},"inputLimitBytes":{"default":12000,"format":"uint","minimum":0,"type":"integer"},"kind":{"$ref":"#/$defs/ConversationKind"},"lastMessageId":{"type":["string","null"]},"members":{"items":{"$ref":"#/$defs/Member"},"type":"array"},"name":{"type":"string"},"owner":{"type":"boolean"},"provider":{"default":null,"type":["string","null"]},"topic":{"type":"string"},"unread":{"format":"uint32","minimum":0,"type":"integer"}},"required":["id","channelId","kind","name","topic","active","owner","members","unread"],"type":"object"};
const schema37 = {"properties":{"available":{"type":"boolean"},"capability":{"type":["string","null"]},"description":{"type":"string"},"name":{"type":"string"},"scope":{"type":"string"},"usage":{"type":"string"}},"required":["name","usage","description","scope","available"],"type":"object"};
const schema38 = {"enum":["channel","query","archive"],"type":"string"};
const schema39 = {"properties":{"capabilities":{"default":[],"items":{"type":"string"},"type":"array"},"id":{"type":"string"},"isSelf":{"type":"boolean"},"nickname":{"type":"string"}},"required":["id","nickname","isSelf"],"type":"object"};

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
if(errors === 0){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing0;
if((((((((((data.id === undefined) && (missing0 = "id")) || ((data.channelId === undefined) && (missing0 = "channelId"))) || ((data.kind === undefined) && (missing0 = "kind"))) || ((data.name === undefined) && (missing0 = "name"))) || ((data.topic === undefined) && (missing0 = "topic"))) || ((data.active === undefined) && (missing0 = "active"))) || ((data.owner === undefined) && (missing0 = "owner"))) || ((data.members === undefined) && (missing0 = "members"))) || ((data.unread === undefined) && (missing0 = "unread"))){
validate25.errors = [{instancePath,schemaPath:"#/required",keyword:"required",params:{missingProperty: missing0},message:"must have required property '"+missing0+"'"}];
return false;
}
else {
if(data.active !== undefined){
const _errs1 = errors;
if(typeof data.active !== "boolean"){
validate25.errors = [{instancePath:instancePath+"/active",schemaPath:"#/properties/active/type",keyword:"type",params:{type: "boolean"},message:"must be boolean"}];
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
validate25.errors = [{instancePath:instancePath+"/channelId",schemaPath:"#/properties/channelId/type",keyword:"type",params:{type: "string"},message:"must be string"}];
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
validate25.errors = [{instancePath:instancePath+"/commands/" + i0,schemaPath:"#/$defs/CommandSpec/required",keyword:"required",params:{missingProperty: missing1},message:"must have required property '"+missing1+"'"}];
return false;
}
else {
if(data3.available !== undefined){
const _errs10 = errors;
if(typeof data3.available !== "boolean"){
validate25.errors = [{instancePath:instancePath+"/commands/" + i0+"/available",schemaPath:"#/$defs/CommandSpec/properties/available/type",keyword:"type",params:{type: "boolean"},message:"must be boolean"}];
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
validate25.errors = [{instancePath:instancePath+"/commands/" + i0+"/capability",schemaPath:"#/$defs/CommandSpec/properties/capability/type",keyword:"type",params:{type: schema37.properties.capability.type},message:"must be string,null"}];
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
validate25.errors = [{instancePath:instancePath+"/commands/" + i0+"/description",schemaPath:"#/$defs/CommandSpec/properties/description/type",keyword:"type",params:{type: "string"},message:"must be string"}];
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
validate25.errors = [{instancePath:instancePath+"/commands/" + i0+"/name",schemaPath:"#/$defs/CommandSpec/properties/name/type",keyword:"type",params:{type: "string"},message:"must be string"}];
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
validate25.errors = [{instancePath:instancePath+"/commands/" + i0+"/scope",schemaPath:"#/$defs/CommandSpec/properties/scope/type",keyword:"type",params:{type: "string"},message:"must be string"}];
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
validate25.errors = [{instancePath:instancePath+"/commands/" + i0+"/usage",schemaPath:"#/$defs/CommandSpec/properties/usage/type",keyword:"type",params:{type: "string"},message:"must be string"}];
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
validate25.errors = [{instancePath:instancePath+"/commands/" + i0,schemaPath:"#/$defs/CommandSpec/type",keyword:"type",params:{type: "object"},message:"must be object"}];
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
validate25.errors = [{instancePath:instancePath+"/commands",schemaPath:"#/properties/commands/type",keyword:"type",params:{type: "array"},message:"must be array"}];
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
const _errs22 = errors;
if(typeof data.id !== "string"){
validate25.errors = [{instancePath:instancePath+"/id",schemaPath:"#/properties/id/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs22 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.inputLimitBytes !== undefined){
let data11 = data.inputLimitBytes;
const _errs24 = errors;
if(!(((typeof data11 == "number") && (!(data11 % 1) && !isNaN(data11))) && (isFinite(data11)))){
validate25.errors = [{instancePath:instancePath+"/inputLimitBytes",schemaPath:"#/properties/inputLimitBytes/type",keyword:"type",params:{type: "integer"},message:"must be integer"}];
return false;
}
if(errors === _errs24){
if((typeof data11 == "number") && (isFinite(data11))){
if(data11 < 0 || isNaN(data11)){
validate25.errors = [{instancePath:instancePath+"/inputLimitBytes",schemaPath:"#/properties/inputLimitBytes/minimum",keyword:"minimum",params:{comparison: ">=", limit: 0},message:"must be >= 0"}];
return false;
}
}
}
var valid0 = _errs24 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.kind !== undefined){
let data12 = data.kind;
const _errs26 = errors;
if(typeof data12 !== "string"){
validate25.errors = [{instancePath:instancePath+"/kind",schemaPath:"#/$defs/ConversationKind/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
if(!(((data12 === "channel") || (data12 === "query")) || (data12 === "archive"))){
validate25.errors = [{instancePath:instancePath+"/kind",schemaPath:"#/$defs/ConversationKind/enum",keyword:"enum",params:{allowedValues: schema38.enum},message:"must be equal to one of the allowed values"}];
return false;
}
var valid0 = _errs26 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.lastMessageId !== undefined){
let data13 = data.lastMessageId;
const _errs29 = errors;
if((typeof data13 !== "string") && (data13 !== null)){
validate25.errors = [{instancePath:instancePath+"/lastMessageId",schemaPath:"#/properties/lastMessageId/type",keyword:"type",params:{type: schema36.properties.lastMessageId.type},message:"must be string,null"}];
return false;
}
var valid0 = _errs29 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.members !== undefined){
let data14 = data.members;
const _errs31 = errors;
if(errors === _errs31){
if(Array.isArray(data14)){
var valid5 = true;
const len1 = data14.length;
for(let i1=0; i1<len1; i1++){
let data15 = data14[i1];
const _errs33 = errors;
const _errs34 = errors;
if(errors === _errs34){
if(data15 && typeof data15 == "object" && !Array.isArray(data15)){
let missing2;
if((((data15.id === undefined) && (missing2 = "id")) || ((data15.nickname === undefined) && (missing2 = "nickname"))) || ((data15.isSelf === undefined) && (missing2 = "isSelf"))){
validate25.errors = [{instancePath:instancePath+"/members/" + i1,schemaPath:"#/$defs/Member/required",keyword:"required",params:{missingProperty: missing2},message:"must have required property '"+missing2+"'"}];
return false;
}
else {
if(data15.capabilities !== undefined){
let data16 = data15.capabilities;
const _errs36 = errors;
if(errors === _errs36){
if(Array.isArray(data16)){
var valid8 = true;
const len2 = data16.length;
for(let i2=0; i2<len2; i2++){
const _errs38 = errors;
if(typeof data16[i2] !== "string"){
validate25.errors = [{instancePath:instancePath+"/members/" + i1+"/capabilities/" + i2,schemaPath:"#/$defs/Member/properties/capabilities/items/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid8 = _errs38 === errors;
if(!valid8){
break;
}
}
}
else {
validate25.errors = [{instancePath:instancePath+"/members/" + i1+"/capabilities",schemaPath:"#/$defs/Member/properties/capabilities/type",keyword:"type",params:{type: "array"},message:"must be array"}];
return false;
}
}
var valid7 = _errs36 === errors;
}
else {
var valid7 = true;
}
if(valid7){
if(data15.id !== undefined){
const _errs40 = errors;
if(typeof data15.id !== "string"){
validate25.errors = [{instancePath:instancePath+"/members/" + i1+"/id",schemaPath:"#/$defs/Member/properties/id/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid7 = _errs40 === errors;
}
else {
var valid7 = true;
}
if(valid7){
if(data15.isSelf !== undefined){
const _errs42 = errors;
if(typeof data15.isSelf !== "boolean"){
validate25.errors = [{instancePath:instancePath+"/members/" + i1+"/isSelf",schemaPath:"#/$defs/Member/properties/isSelf/type",keyword:"type",params:{type: "boolean"},message:"must be boolean"}];
return false;
}
var valid7 = _errs42 === errors;
}
else {
var valid7 = true;
}
if(valid7){
if(data15.nickname !== undefined){
const _errs44 = errors;
if(typeof data15.nickname !== "string"){
validate25.errors = [{instancePath:instancePath+"/members/" + i1+"/nickname",schemaPath:"#/$defs/Member/properties/nickname/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
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
}
else {
validate25.errors = [{instancePath:instancePath+"/members/" + i1,schemaPath:"#/$defs/Member/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
var valid5 = _errs33 === errors;
if(!valid5){
break;
}
}
}
else {
validate25.errors = [{instancePath:instancePath+"/members",schemaPath:"#/properties/members/type",keyword:"type",params:{type: "array"},message:"must be array"}];
return false;
}
}
var valid0 = _errs31 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.name !== undefined){
const _errs46 = errors;
if(typeof data.name !== "string"){
validate25.errors = [{instancePath:instancePath+"/name",schemaPath:"#/properties/name/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs46 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.owner !== undefined){
const _errs48 = errors;
if(typeof data.owner !== "boolean"){
validate25.errors = [{instancePath:instancePath+"/owner",schemaPath:"#/properties/owner/type",keyword:"type",params:{type: "boolean"},message:"must be boolean"}];
return false;
}
var valid0 = _errs48 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.provider !== undefined){
let data23 = data.provider;
const _errs50 = errors;
if((typeof data23 !== "string") && (data23 !== null)){
validate25.errors = [{instancePath:instancePath+"/provider",schemaPath:"#/properties/provider/type",keyword:"type",params:{type: schema36.properties.provider.type},message:"must be string,null"}];
return false;
}
var valid0 = _errs50 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.topic !== undefined){
const _errs52 = errors;
if(typeof data.topic !== "string"){
validate25.errors = [{instancePath:instancePath+"/topic",schemaPath:"#/properties/topic/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs52 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.unread !== undefined){
let data25 = data.unread;
const _errs54 = errors;
if(!(((typeof data25 == "number") && (!(data25 % 1) && !isNaN(data25))) && (isFinite(data25)))){
validate25.errors = [{instancePath:instancePath+"/unread",schemaPath:"#/properties/unread/type",keyword:"type",params:{type: "integer"},message:"must be integer"}];
return false;
}
if(errors === _errs54){
if((typeof data25 == "number") && (isFinite(data25))){
if(data25 < 0 || isNaN(data25)){
validate25.errors = [{instancePath:instancePath+"/unread",schemaPath:"#/properties/unread/minimum",keyword:"minimum",params:{comparison: ">=", limit: 0},message:"must be >= 0"}];
return false;
}
}
}
var valid0 = _errs54 === errors;
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
else {
validate25.errors = [{instancePath,schemaPath:"#/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
validate25.errors = vErrors;
return errors === 0;
}
validate25.evaluated = {"props":{"active":true,"channelId":true,"commands":true,"id":true,"inputLimitBytes":true,"kind":true,"lastMessageId":true,"members":true,"name":true,"owner":true,"provider":true,"topic":true,"unread":true},"dynamicProps":false,"dynamicItems":false};


function validate24(data, {instancePath="", parentData, parentDataProperty, rootData=data, dynamicAnchors={}}={}){
let vErrors = null;
let errors = 0;
const evaluated0 = validate24.evaluated;
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
validate24.errors = [{instancePath,schemaPath:"#/required",keyword:"required",params:{missingProperty: missing0},message:"must have required property '"+missing0+"'"}];
return false;
}
else {
if(data.commandHistory !== undefined){
let data0 = data.commandHistory;
const _errs1 = errors;
if(errors === _errs1){
if(Array.isArray(data0)){
var valid1 = true;
const len0 = data0.length;
for(let i0=0; i0<len0; i0++){
const _errs3 = errors;
if(typeof data0[i0] !== "string"){
validate24.errors = [{instancePath:instancePath+"/commandHistory/" + i0,schemaPath:"#/properties/commandHistory/items/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid1 = _errs3 === errors;
if(!valid1){
break;
}
}
}
else {
validate24.errors = [{instancePath:instancePath+"/commandHistory",schemaPath:"#/properties/commandHistory/type",keyword:"type",params:{type: "array"},message:"must be array"}];
return false;
}
}
var valid0 = _errs1 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.conversations !== undefined){
let data2 = data.conversations;
const _errs5 = errors;
if(errors === _errs5){
if(Array.isArray(data2)){
var valid2 = true;
const len1 = data2.length;
for(let i1=0; i1<len1; i1++){
const _errs7 = errors;
if(!(validate25(data2[i1], {instancePath:instancePath+"/conversations/" + i1,parentData:data2,parentDataProperty:i1,rootData,dynamicAnchors}))){
vErrors = vErrors === null ? validate25.errors : vErrors.concat(validate25.errors);
errors = vErrors.length;
}
var valid2 = _errs7 === errors;
if(!valid2){
break;
}
}
}
else {
validate24.errors = [{instancePath:instancePath+"/conversations",schemaPath:"#/properties/conversations/type",keyword:"type",params:{type: "array"},message:"must be array"}];
return false;
}
}
var valid0 = _errs5 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.inputHistory !== undefined){
let data4 = data.inputHistory;
const _errs8 = errors;
if(errors === _errs8){
if(Array.isArray(data4)){
var valid3 = true;
const len2 = data4.length;
for(let i2=0; i2<len2; i2++){
let data5 = data4[i2];
const _errs10 = errors;
const _errs11 = errors;
if(errors === _errs11){
if(data5 && typeof data5 == "object" && !Array.isArray(data5)){
let missing1;
if((data5.text === undefined) && (missing1 = "text")){
validate24.errors = [{instancePath:instancePath+"/inputHistory/" + i2,schemaPath:"#/$defs/InputHistoryEntry/required",keyword:"required",params:{missingProperty: missing1},message:"must have required property '"+missing1+"'"}];
return false;
}
else {
if(data5.conversation !== undefined){
let data6 = data5.conversation;
const _errs13 = errors;
if((typeof data6 !== "string") && (data6 !== null)){
validate24.errors = [{instancePath:instancePath+"/inputHistory/" + i2+"/conversation",schemaPath:"#/$defs/InputHistoryEntry/properties/conversation/type",keyword:"type",params:{type: schema40.properties.conversation.type},message:"must be string,null"}];
return false;
}
var valid5 = _errs13 === errors;
}
else {
var valid5 = true;
}
if(valid5){
if(data5.text !== undefined){
const _errs15 = errors;
if(typeof data5.text !== "string"){
validate24.errors = [{instancePath:instancePath+"/inputHistory/" + i2+"/text",schemaPath:"#/$defs/InputHistoryEntry/properties/text/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid5 = _errs15 === errors;
}
else {
var valid5 = true;
}
}
}
}
else {
validate24.errors = [{instancePath:instancePath+"/inputHistory/" + i2,schemaPath:"#/$defs/InputHistoryEntry/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
var valid3 = _errs10 === errors;
if(!valid3){
break;
}
}
}
else {
validate24.errors = [{instancePath:instancePath+"/inputHistory",schemaPath:"#/properties/inputHistory/type",keyword:"type",params:{type: "array"},message:"must be array"}];
return false;
}
}
var valid0 = _errs8 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.instance !== undefined){
let data8 = data.instance;
const _errs17 = errors;
const _errs18 = errors;
if(errors === _errs18){
if(data8 && typeof data8 == "object" && !Array.isArray(data8)){
let missing2;
if((((((((((data8.id === undefined) && (missing2 = "id")) || ((data8.label === undefined) && (missing2 = "label"))) || ((data8.bootId === undefined) && (missing2 = "bootId"))) || ((data8.locked === undefined) && (missing2 = "locked"))) || ((data8.protocolLocked === undefined) && (missing2 = "protocolLocked"))) || ((data8.profileExists === undefined) && (missing2 = "profileExists"))) || ((data8.archiveExists === undefined) && (missing2 = "archiveExists"))) || ((data8.safetyNumber === undefined) && (missing2 = "safetyNumber"))) || ((data8.capabilities === undefined) && (missing2 = "capabilities"))){
validate24.errors = [{instancePath:instancePath+"/instance",schemaPath:"#/$defs/InstanceInfo/required",keyword:"required",params:{missingProperty: missing2},message:"must have required property '"+missing2+"'"}];
return false;
}
else {
if(data8.archiveExists !== undefined){
const _errs20 = errors;
if(typeof data8.archiveExists !== "boolean"){
validate24.errors = [{instancePath:instancePath+"/instance/archiveExists",schemaPath:"#/$defs/InstanceInfo/properties/archiveExists/type",keyword:"type",params:{type: "boolean"},message:"must be boolean"}];
return false;
}
var valid7 = _errs20 === errors;
}
else {
var valid7 = true;
}
if(valid7){
if(data8.bootId !== undefined){
const _errs22 = errors;
if(typeof data8.bootId !== "string"){
validate24.errors = [{instancePath:instancePath+"/instance/bootId",schemaPath:"#/$defs/InstanceInfo/properties/bootId/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid7 = _errs22 === errors;
}
else {
var valid7 = true;
}
if(valid7){
if(data8.capabilities !== undefined){
let data11 = data8.capabilities;
const _errs24 = errors;
if(errors === _errs24){
if(Array.isArray(data11)){
var valid8 = true;
const len3 = data11.length;
for(let i3=0; i3<len3; i3++){
const _errs26 = errors;
if(typeof data11[i3] !== "string"){
validate24.errors = [{instancePath:instancePath+"/instance/capabilities/" + i3,schemaPath:"#/$defs/InstanceInfo/properties/capabilities/items/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid8 = _errs26 === errors;
if(!valid8){
break;
}
}
}
else {
validate24.errors = [{instancePath:instancePath+"/instance/capabilities",schemaPath:"#/$defs/InstanceInfo/properties/capabilities/type",keyword:"type",params:{type: "array"},message:"must be array"}];
return false;
}
}
var valid7 = _errs24 === errors;
}
else {
var valid7 = true;
}
if(valid7){
if(data8.id !== undefined){
const _errs28 = errors;
if(typeof data8.id !== "string"){
validate24.errors = [{instancePath:instancePath+"/instance/id",schemaPath:"#/$defs/InstanceInfo/properties/id/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid7 = _errs28 === errors;
}
else {
var valid7 = true;
}
if(valid7){
if(data8.label !== undefined){
const _errs30 = errors;
if(typeof data8.label !== "string"){
validate24.errors = [{instancePath:instancePath+"/instance/label",schemaPath:"#/$defs/InstanceInfo/properties/label/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid7 = _errs30 === errors;
}
else {
var valid7 = true;
}
if(valid7){
if(data8.locked !== undefined){
const _errs32 = errors;
if(typeof data8.locked !== "boolean"){
validate24.errors = [{instancePath:instancePath+"/instance/locked",schemaPath:"#/$defs/InstanceInfo/properties/locked/type",keyword:"type",params:{type: "boolean"},message:"must be boolean"}];
return false;
}
var valid7 = _errs32 === errors;
}
else {
var valid7 = true;
}
if(valid7){
if(data8.profileExists !== undefined){
const _errs34 = errors;
if(typeof data8.profileExists !== "boolean"){
validate24.errors = [{instancePath:instancePath+"/instance/profileExists",schemaPath:"#/$defs/InstanceInfo/properties/profileExists/type",keyword:"type",params:{type: "boolean"},message:"must be boolean"}];
return false;
}
var valid7 = _errs34 === errors;
}
else {
var valid7 = true;
}
if(valid7){
if(data8.protocolLocked !== undefined){
const _errs36 = errors;
if(typeof data8.protocolLocked !== "boolean"){
validate24.errors = [{instancePath:instancePath+"/instance/protocolLocked",schemaPath:"#/$defs/InstanceInfo/properties/protocolLocked/type",keyword:"type",params:{type: "boolean"},message:"must be boolean"}];
return false;
}
var valid7 = _errs36 === errors;
}
else {
var valid7 = true;
}
if(valid7){
if(data8.safetyNumber !== undefined){
const _errs38 = errors;
if(typeof data8.safetyNumber !== "string"){
validate24.errors = [{instancePath:instancePath+"/instance/safetyNumber",schemaPath:"#/$defs/InstanceInfo/properties/safetyNumber/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid7 = _errs38 === errors;
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
}
}
}
}
else {
validate24.errors = [{instancePath:instancePath+"/instance",schemaPath:"#/$defs/InstanceInfo/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
var valid0 = _errs17 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.providerErrors !== undefined){
let data19 = data.providerErrors;
const _errs40 = errors;
if(errors === _errs40){
if(Array.isArray(data19)){
var valid9 = true;
const len4 = data19.length;
for(let i4=0; i4<len4; i4++){
let data20 = data19[i4];
const _errs42 = errors;
const _errs43 = errors;
if(errors === _errs43){
if(data20 && typeof data20 == "object" && !Array.isArray(data20)){
let missing3;
if(((((data20.id === undefined) && (missing3 = "id")) || ((data20.code === undefined) && (missing3 = "code"))) || ((data20.message === undefined) && (missing3 = "message"))) || ((data20.retryable === undefined) && (missing3 = "retryable"))){
validate24.errors = [{instancePath:instancePath+"/providerErrors/" + i4,schemaPath:"#/$defs/ProviderStatus/required",keyword:"required",params:{missingProperty: missing3},message:"must have required property '"+missing3+"'"}];
return false;
}
else {
if(data20.code !== undefined){
const _errs45 = errors;
if(typeof data20.code !== "string"){
validate24.errors = [{instancePath:instancePath+"/providerErrors/" + i4+"/code",schemaPath:"#/$defs/ProviderStatus/properties/code/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid11 = _errs45 === errors;
}
else {
var valid11 = true;
}
if(valid11){
if(data20.id !== undefined){
const _errs47 = errors;
if(typeof data20.id !== "string"){
validate24.errors = [{instancePath:instancePath+"/providerErrors/" + i4+"/id",schemaPath:"#/$defs/ProviderStatus/properties/id/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid11 = _errs47 === errors;
}
else {
var valid11 = true;
}
if(valid11){
if(data20.message !== undefined){
const _errs49 = errors;
if(typeof data20.message !== "string"){
validate24.errors = [{instancePath:instancePath+"/providerErrors/" + i4+"/message",schemaPath:"#/$defs/ProviderStatus/properties/message/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid11 = _errs49 === errors;
}
else {
var valid11 = true;
}
if(valid11){
if(data20.retryable !== undefined){
const _errs51 = errors;
if(typeof data20.retryable !== "boolean"){
validate24.errors = [{instancePath:instancePath+"/providerErrors/" + i4+"/retryable",schemaPath:"#/$defs/ProviderStatus/properties/retryable/type",keyword:"type",params:{type: "boolean"},message:"must be boolean"}];
return false;
}
var valid11 = _errs51 === errors;
}
else {
var valid11 = true;
}
}
}
}
}
}
else {
validate24.errors = [{instancePath:instancePath+"/providerErrors/" + i4,schemaPath:"#/$defs/ProviderStatus/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
var valid9 = _errs42 === errors;
if(!valid9){
break;
}
}
}
else {
validate24.errors = [{instancePath:instancePath+"/providerErrors",schemaPath:"#/properties/providerErrors/type",keyword:"type",params:{type: "array"},message:"must be array"}];
return false;
}
}
var valid0 = _errs40 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.revision !== undefined){
const _errs53 = errors;
if(typeof data.revision !== "string"){
validate24.errors = [{instancePath:instancePath+"/revision",schemaPath:"#/properties/revision/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs53 === errors;
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
else {
validate24.errors = [{instancePath,schemaPath:"#/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
validate24.errors = vErrors;
return errors === 0;
}
validate24.evaluated = {"props":{"commandHistory":true,"conversations":true,"inputHistory":true,"instance":true,"providerErrors":true,"revision":true},"dynamicProps":false,"dynamicItems":false};

export const unlock_error = validate27;
const schema43 = {"$schema":"https://json-schema.org/draft/2020-12/schema","additionalProperties":false,"properties":{"code":{"type":"string"},"message":{"type":"string"}},"required":["code","message"],"title":"ChatError","type":"object"};

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
if(((data.code === undefined) && (missing0 = "code")) || ((data.message === undefined) && (missing0 = "message"))){
validate27.errors = [{instancePath,schemaPath:"#/required",keyword:"required",params:{missingProperty: missing0},message:"must have required property '"+missing0+"'"}];
return false;
}
else {
const _errs1 = errors;
for(const key0 in data){
if(!((key0 === "code") || (key0 === "message"))){
validate27.errors = [{instancePath,schemaPath:"#/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key0},message:"must NOT have additional properties"}];
return false;
break;
}
}
if(_errs1 === errors){
if(data.code !== undefined){
const _errs2 = errors;
if(typeof data.code !== "string"){
validate27.errors = [{instancePath:instancePath+"/code",schemaPath:"#/properties/code/type",keyword:"type",params:{type: "string"},message:"must be string"}];
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
validate27.errors = [{instancePath:instancePath+"/message",schemaPath:"#/properties/message/type",keyword:"type",params:{type: "string"},message:"must be string"}];
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
validate27.errors = [{instancePath,schemaPath:"#/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
validate27.errors = vErrors;
return errors === 0;
}
validate27.evaluated = {"props":true,"dynamicProps":false,"dynamicItems":false};

export const lock_args = validate28;
const schema44 = {"$schema":"https://json-schema.org/draft/2020-12/schema","additionalProperties":false,"title":"ChatLockArgs","type":"object"};

function validate28(data, {instancePath="", parentData, parentDataProperty, rootData=data, dynamicAnchors={}}={}){
let vErrors = null;
let errors = 0;
const evaluated0 = validate28.evaluated;
if(evaluated0.dynamicProps){
evaluated0.props = undefined;
}
if(evaluated0.dynamicItems){
evaluated0.items = undefined;
}
if(errors === 0){
if(data && typeof data == "object" && !Array.isArray(data)){
for(const key0 in data){
validate28.errors = [{instancePath,schemaPath:"#/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key0},message:"must NOT have additional properties"}];
return false;
break;
}
}
else {
validate28.errors = [{instancePath,schemaPath:"#/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
validate28.errors = vErrors;
return errors === 0;
}
validate28.evaluated = {"props":true,"dynamicProps":false,"dynamicItems":false};

export const lock_output = validate29;
const schema45 = {"$schema":"https://json-schema.org/draft/2020-12/schema","properties":{"archiveExists":{"type":"boolean"},"bootId":{"type":"string"},"capabilities":{"items":{"type":"string"},"type":"array"},"id":{"type":"string"},"label":{"type":"string"},"locked":{"type":"boolean"},"profileExists":{"type":"boolean"},"protocolLocked":{"type":"boolean"},"safetyNumber":{"type":"string"}},"required":["id","label","bootId","locked","protocolLocked","profileExists","archiveExists","safetyNumber","capabilities"],"title":"InstanceInfo","type":"object"};

function validate29(data, {instancePath="", parentData, parentDataProperty, rootData=data, dynamicAnchors={}}={}){
let vErrors = null;
let errors = 0;
const evaluated0 = validate29.evaluated;
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
validate29.errors = [{instancePath,schemaPath:"#/required",keyword:"required",params:{missingProperty: missing0},message:"must have required property '"+missing0+"'"}];
return false;
}
else {
if(data.archiveExists !== undefined){
const _errs1 = errors;
if(typeof data.archiveExists !== "boolean"){
validate29.errors = [{instancePath:instancePath+"/archiveExists",schemaPath:"#/properties/archiveExists/type",keyword:"type",params:{type: "boolean"},message:"must be boolean"}];
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
validate29.errors = [{instancePath:instancePath+"/bootId",schemaPath:"#/properties/bootId/type",keyword:"type",params:{type: "string"},message:"must be string"}];
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
validate29.errors = [{instancePath:instancePath+"/capabilities/" + i0,schemaPath:"#/properties/capabilities/items/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid1 = _errs7 === errors;
if(!valid1){
break;
}
}
}
else {
validate29.errors = [{instancePath:instancePath+"/capabilities",schemaPath:"#/properties/capabilities/type",keyword:"type",params:{type: "array"},message:"must be array"}];
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
validate29.errors = [{instancePath:instancePath+"/id",schemaPath:"#/properties/id/type",keyword:"type",params:{type: "string"},message:"must be string"}];
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
validate29.errors = [{instancePath:instancePath+"/label",schemaPath:"#/properties/label/type",keyword:"type",params:{type: "string"},message:"must be string"}];
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
validate29.errors = [{instancePath:instancePath+"/locked",schemaPath:"#/properties/locked/type",keyword:"type",params:{type: "boolean"},message:"must be boolean"}];
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
validate29.errors = [{instancePath:instancePath+"/profileExists",schemaPath:"#/properties/profileExists/type",keyword:"type",params:{type: "boolean"},message:"must be boolean"}];
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
validate29.errors = [{instancePath:instancePath+"/protocolLocked",schemaPath:"#/properties/protocolLocked/type",keyword:"type",params:{type: "boolean"},message:"must be boolean"}];
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
validate29.errors = [{instancePath:instancePath+"/safetyNumber",schemaPath:"#/properties/safetyNumber/type",keyword:"type",params:{type: "string"},message:"must be string"}];
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
validate29.errors = [{instancePath,schemaPath:"#/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
validate29.errors = vErrors;
return errors === 0;
}
validate29.evaluated = {"props":{"archiveExists":true,"bootId":true,"capabilities":true,"id":true,"label":true,"locked":true,"profileExists":true,"protocolLocked":true,"safetyNumber":true},"dynamicProps":false,"dynamicItems":false};

export const lock_error = validate30;
const schema46 = {"$schema":"https://json-schema.org/draft/2020-12/schema","additionalProperties":false,"properties":{"code":{"type":"string"},"message":{"type":"string"}},"required":["code","message"],"title":"ChatError","type":"object"};

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
if(((data.code === undefined) && (missing0 = "code")) || ((data.message === undefined) && (missing0 = "message"))){
validate30.errors = [{instancePath,schemaPath:"#/required",keyword:"required",params:{missingProperty: missing0},message:"must have required property '"+missing0+"'"}];
return false;
}
else {
const _errs1 = errors;
for(const key0 in data){
if(!((key0 === "code") || (key0 === "message"))){
validate30.errors = [{instancePath,schemaPath:"#/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key0},message:"must NOT have additional properties"}];
return false;
break;
}
}
if(_errs1 === errors){
if(data.code !== undefined){
const _errs2 = errors;
if(typeof data.code !== "string"){
validate30.errors = [{instancePath:instancePath+"/code",schemaPath:"#/properties/code/type",keyword:"type",params:{type: "string"},message:"must be string"}];
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
validate30.errors = [{instancePath:instancePath+"/message",schemaPath:"#/properties/message/type",keyword:"type",params:{type: "string"},message:"must be string"}];
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
validate30.errors = [{instancePath,schemaPath:"#/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
validate30.errors = vErrors;
return errors === 0;
}
validate30.evaluated = {"props":true,"dynamicProps":false,"dynamicItems":false};

export const disconnect_args = validate31;
const schema47 = {"$schema":"https://json-schema.org/draft/2020-12/schema","additionalProperties":false,"title":"ChatDisconnectArgs","type":"object"};

function validate31(data, {instancePath="", parentData, parentDataProperty, rootData=data, dynamicAnchors={}}={}){
let vErrors = null;
let errors = 0;
const evaluated0 = validate31.evaluated;
if(evaluated0.dynamicProps){
evaluated0.props = undefined;
}
if(evaluated0.dynamicItems){
evaluated0.items = undefined;
}
if(errors === 0){
if(data && typeof data == "object" && !Array.isArray(data)){
for(const key0 in data){
validate31.errors = [{instancePath,schemaPath:"#/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key0},message:"must NOT have additional properties"}];
return false;
break;
}
}
else {
validate31.errors = [{instancePath,schemaPath:"#/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
validate31.errors = vErrors;
return errors === 0;
}
validate31.evaluated = {"props":true,"dynamicProps":false,"dynamicItems":false};

export const disconnect_output = validate32;
const schema48 = {"$defs":{"CommandSpec":{"properties":{"available":{"type":"boolean"},"capability":{"type":["string","null"]},"description":{"type":"string"},"name":{"type":"string"},"scope":{"type":"string"},"usage":{"type":"string"}},"required":["name","usage","description","scope","available"],"type":"object"},"Conversation":{"properties":{"active":{"type":"boolean"},"channelId":{"type":"string"},"commands":{"default":[],"items":{"$ref":"#/$defs/CommandSpec"},"type":"array"},"id":{"type":"string"},"inputLimitBytes":{"default":12000,"format":"uint","minimum":0,"type":"integer"},"kind":{"$ref":"#/$defs/ConversationKind"},"lastMessageId":{"type":["string","null"]},"members":{"items":{"$ref":"#/$defs/Member"},"type":"array"},"name":{"type":"string"},"owner":{"type":"boolean"},"provider":{"default":null,"type":["string","null"]},"topic":{"type":"string"},"unread":{"format":"uint32","minimum":0,"type":"integer"}},"required":["id","channelId","kind","name","topic","active","owner","members","unread"],"type":"object"},"ConversationKind":{"enum":["channel","query","archive"],"type":"string"},"InputHistoryEntry":{"properties":{"conversation":{"type":["string","null"]},"text":{"type":"string"}},"required":["text"],"type":"object"},"InstanceInfo":{"properties":{"archiveExists":{"type":"boolean"},"bootId":{"type":"string"},"capabilities":{"items":{"type":"string"},"type":"array"},"id":{"type":"string"},"label":{"type":"string"},"locked":{"type":"boolean"},"profileExists":{"type":"boolean"},"protocolLocked":{"type":"boolean"},"safetyNumber":{"type":"string"}},"required":["id","label","bootId","locked","protocolLocked","profileExists","archiveExists","safetyNumber","capabilities"],"type":"object"},"Member":{"properties":{"capabilities":{"default":[],"items":{"type":"string"},"type":"array"},"id":{"type":"string"},"isSelf":{"type":"boolean"},"nickname":{"type":"string"}},"required":["id","nickname","isSelf"],"type":"object"},"ProviderStatus":{"properties":{"code":{"type":"string"},"id":{"type":"string"},"message":{"type":"string"},"retryable":{"type":"boolean"}},"required":["id","code","message","retryable"],"type":"object"}},"$schema":"https://json-schema.org/draft/2020-12/schema","properties":{"commandHistory":{"items":{"type":"string"},"type":"array"},"conversations":{"items":{"$ref":"#/$defs/Conversation"},"type":"array"},"inputHistory":{"items":{"$ref":"#/$defs/InputHistoryEntry"},"type":"array"},"instance":{"$ref":"#/$defs/InstanceInfo"},"providerErrors":{"default":[],"items":{"$ref":"#/$defs/ProviderStatus"},"type":"array"},"revision":{"type":"string"}},"required":["instance","revision","conversations","commandHistory","inputHistory"],"title":"Snapshot","type":"object"};
const schema53 = {"properties":{"conversation":{"type":["string","null"]},"text":{"type":"string"}},"required":["text"],"type":"object"};
const schema54 = {"properties":{"archiveExists":{"type":"boolean"},"bootId":{"type":"string"},"capabilities":{"items":{"type":"string"},"type":"array"},"id":{"type":"string"},"label":{"type":"string"},"locked":{"type":"boolean"},"profileExists":{"type":"boolean"},"protocolLocked":{"type":"boolean"},"safetyNumber":{"type":"string"}},"required":["id","label","bootId","locked","protocolLocked","profileExists","archiveExists","safetyNumber","capabilities"],"type":"object"};
const schema55 = {"properties":{"code":{"type":"string"},"id":{"type":"string"},"message":{"type":"string"},"retryable":{"type":"boolean"}},"required":["id","code","message","retryable"],"type":"object"};
const schema49 = {"properties":{"active":{"type":"boolean"},"channelId":{"type":"string"},"commands":{"default":[],"items":{"$ref":"#/$defs/CommandSpec"},"type":"array"},"id":{"type":"string"},"inputLimitBytes":{"default":12000,"format":"uint","minimum":0,"type":"integer"},"kind":{"$ref":"#/$defs/ConversationKind"},"lastMessageId":{"type":["string","null"]},"members":{"items":{"$ref":"#/$defs/Member"},"type":"array"},"name":{"type":"string"},"owner":{"type":"boolean"},"provider":{"default":null,"type":["string","null"]},"topic":{"type":"string"},"unread":{"format":"uint32","minimum":0,"type":"integer"}},"required":["id","channelId","kind","name","topic","active","owner","members","unread"],"type":"object"};
const schema50 = {"properties":{"available":{"type":"boolean"},"capability":{"type":["string","null"]},"description":{"type":"string"},"name":{"type":"string"},"scope":{"type":"string"},"usage":{"type":"string"}},"required":["name","usage","description","scope","available"],"type":"object"};
const schema51 = {"enum":["channel","query","archive"],"type":"string"};
const schema52 = {"properties":{"capabilities":{"default":[],"items":{"type":"string"},"type":"array"},"id":{"type":"string"},"isSelf":{"type":"boolean"},"nickname":{"type":"string"}},"required":["id","nickname","isSelf"],"type":"object"};

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
if(errors === 0){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing0;
if((((((((((data.id === undefined) && (missing0 = "id")) || ((data.channelId === undefined) && (missing0 = "channelId"))) || ((data.kind === undefined) && (missing0 = "kind"))) || ((data.name === undefined) && (missing0 = "name"))) || ((data.topic === undefined) && (missing0 = "topic"))) || ((data.active === undefined) && (missing0 = "active"))) || ((data.owner === undefined) && (missing0 = "owner"))) || ((data.members === undefined) && (missing0 = "members"))) || ((data.unread === undefined) && (missing0 = "unread"))){
validate33.errors = [{instancePath,schemaPath:"#/required",keyword:"required",params:{missingProperty: missing0},message:"must have required property '"+missing0+"'"}];
return false;
}
else {
if(data.active !== undefined){
const _errs1 = errors;
if(typeof data.active !== "boolean"){
validate33.errors = [{instancePath:instancePath+"/active",schemaPath:"#/properties/active/type",keyword:"type",params:{type: "boolean"},message:"must be boolean"}];
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
validate33.errors = [{instancePath:instancePath+"/channelId",schemaPath:"#/properties/channelId/type",keyword:"type",params:{type: "string"},message:"must be string"}];
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
validate33.errors = [{instancePath:instancePath+"/commands/" + i0,schemaPath:"#/$defs/CommandSpec/required",keyword:"required",params:{missingProperty: missing1},message:"must have required property '"+missing1+"'"}];
return false;
}
else {
if(data3.available !== undefined){
const _errs10 = errors;
if(typeof data3.available !== "boolean"){
validate33.errors = [{instancePath:instancePath+"/commands/" + i0+"/available",schemaPath:"#/$defs/CommandSpec/properties/available/type",keyword:"type",params:{type: "boolean"},message:"must be boolean"}];
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
validate33.errors = [{instancePath:instancePath+"/commands/" + i0+"/capability",schemaPath:"#/$defs/CommandSpec/properties/capability/type",keyword:"type",params:{type: schema50.properties.capability.type},message:"must be string,null"}];
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
validate33.errors = [{instancePath:instancePath+"/commands/" + i0+"/description",schemaPath:"#/$defs/CommandSpec/properties/description/type",keyword:"type",params:{type: "string"},message:"must be string"}];
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
validate33.errors = [{instancePath:instancePath+"/commands/" + i0+"/name",schemaPath:"#/$defs/CommandSpec/properties/name/type",keyword:"type",params:{type: "string"},message:"must be string"}];
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
validate33.errors = [{instancePath:instancePath+"/commands/" + i0+"/scope",schemaPath:"#/$defs/CommandSpec/properties/scope/type",keyword:"type",params:{type: "string"},message:"must be string"}];
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
validate33.errors = [{instancePath:instancePath+"/commands/" + i0+"/usage",schemaPath:"#/$defs/CommandSpec/properties/usage/type",keyword:"type",params:{type: "string"},message:"must be string"}];
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
validate33.errors = [{instancePath:instancePath+"/commands/" + i0,schemaPath:"#/$defs/CommandSpec/type",keyword:"type",params:{type: "object"},message:"must be object"}];
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
validate33.errors = [{instancePath:instancePath+"/commands",schemaPath:"#/properties/commands/type",keyword:"type",params:{type: "array"},message:"must be array"}];
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
const _errs22 = errors;
if(typeof data.id !== "string"){
validate33.errors = [{instancePath:instancePath+"/id",schemaPath:"#/properties/id/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs22 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.inputLimitBytes !== undefined){
let data11 = data.inputLimitBytes;
const _errs24 = errors;
if(!(((typeof data11 == "number") && (!(data11 % 1) && !isNaN(data11))) && (isFinite(data11)))){
validate33.errors = [{instancePath:instancePath+"/inputLimitBytes",schemaPath:"#/properties/inputLimitBytes/type",keyword:"type",params:{type: "integer"},message:"must be integer"}];
return false;
}
if(errors === _errs24){
if((typeof data11 == "number") && (isFinite(data11))){
if(data11 < 0 || isNaN(data11)){
validate33.errors = [{instancePath:instancePath+"/inputLimitBytes",schemaPath:"#/properties/inputLimitBytes/minimum",keyword:"minimum",params:{comparison: ">=", limit: 0},message:"must be >= 0"}];
return false;
}
}
}
var valid0 = _errs24 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.kind !== undefined){
let data12 = data.kind;
const _errs26 = errors;
if(typeof data12 !== "string"){
validate33.errors = [{instancePath:instancePath+"/kind",schemaPath:"#/$defs/ConversationKind/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
if(!(((data12 === "channel") || (data12 === "query")) || (data12 === "archive"))){
validate33.errors = [{instancePath:instancePath+"/kind",schemaPath:"#/$defs/ConversationKind/enum",keyword:"enum",params:{allowedValues: schema51.enum},message:"must be equal to one of the allowed values"}];
return false;
}
var valid0 = _errs26 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.lastMessageId !== undefined){
let data13 = data.lastMessageId;
const _errs29 = errors;
if((typeof data13 !== "string") && (data13 !== null)){
validate33.errors = [{instancePath:instancePath+"/lastMessageId",schemaPath:"#/properties/lastMessageId/type",keyword:"type",params:{type: schema49.properties.lastMessageId.type},message:"must be string,null"}];
return false;
}
var valid0 = _errs29 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.members !== undefined){
let data14 = data.members;
const _errs31 = errors;
if(errors === _errs31){
if(Array.isArray(data14)){
var valid5 = true;
const len1 = data14.length;
for(let i1=0; i1<len1; i1++){
let data15 = data14[i1];
const _errs33 = errors;
const _errs34 = errors;
if(errors === _errs34){
if(data15 && typeof data15 == "object" && !Array.isArray(data15)){
let missing2;
if((((data15.id === undefined) && (missing2 = "id")) || ((data15.nickname === undefined) && (missing2 = "nickname"))) || ((data15.isSelf === undefined) && (missing2 = "isSelf"))){
validate33.errors = [{instancePath:instancePath+"/members/" + i1,schemaPath:"#/$defs/Member/required",keyword:"required",params:{missingProperty: missing2},message:"must have required property '"+missing2+"'"}];
return false;
}
else {
if(data15.capabilities !== undefined){
let data16 = data15.capabilities;
const _errs36 = errors;
if(errors === _errs36){
if(Array.isArray(data16)){
var valid8 = true;
const len2 = data16.length;
for(let i2=0; i2<len2; i2++){
const _errs38 = errors;
if(typeof data16[i2] !== "string"){
validate33.errors = [{instancePath:instancePath+"/members/" + i1+"/capabilities/" + i2,schemaPath:"#/$defs/Member/properties/capabilities/items/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid8 = _errs38 === errors;
if(!valid8){
break;
}
}
}
else {
validate33.errors = [{instancePath:instancePath+"/members/" + i1+"/capabilities",schemaPath:"#/$defs/Member/properties/capabilities/type",keyword:"type",params:{type: "array"},message:"must be array"}];
return false;
}
}
var valid7 = _errs36 === errors;
}
else {
var valid7 = true;
}
if(valid7){
if(data15.id !== undefined){
const _errs40 = errors;
if(typeof data15.id !== "string"){
validate33.errors = [{instancePath:instancePath+"/members/" + i1+"/id",schemaPath:"#/$defs/Member/properties/id/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid7 = _errs40 === errors;
}
else {
var valid7 = true;
}
if(valid7){
if(data15.isSelf !== undefined){
const _errs42 = errors;
if(typeof data15.isSelf !== "boolean"){
validate33.errors = [{instancePath:instancePath+"/members/" + i1+"/isSelf",schemaPath:"#/$defs/Member/properties/isSelf/type",keyword:"type",params:{type: "boolean"},message:"must be boolean"}];
return false;
}
var valid7 = _errs42 === errors;
}
else {
var valid7 = true;
}
if(valid7){
if(data15.nickname !== undefined){
const _errs44 = errors;
if(typeof data15.nickname !== "string"){
validate33.errors = [{instancePath:instancePath+"/members/" + i1+"/nickname",schemaPath:"#/$defs/Member/properties/nickname/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
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
}
else {
validate33.errors = [{instancePath:instancePath+"/members/" + i1,schemaPath:"#/$defs/Member/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
var valid5 = _errs33 === errors;
if(!valid5){
break;
}
}
}
else {
validate33.errors = [{instancePath:instancePath+"/members",schemaPath:"#/properties/members/type",keyword:"type",params:{type: "array"},message:"must be array"}];
return false;
}
}
var valid0 = _errs31 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.name !== undefined){
const _errs46 = errors;
if(typeof data.name !== "string"){
validate33.errors = [{instancePath:instancePath+"/name",schemaPath:"#/properties/name/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs46 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.owner !== undefined){
const _errs48 = errors;
if(typeof data.owner !== "boolean"){
validate33.errors = [{instancePath:instancePath+"/owner",schemaPath:"#/properties/owner/type",keyword:"type",params:{type: "boolean"},message:"must be boolean"}];
return false;
}
var valid0 = _errs48 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.provider !== undefined){
let data23 = data.provider;
const _errs50 = errors;
if((typeof data23 !== "string") && (data23 !== null)){
validate33.errors = [{instancePath:instancePath+"/provider",schemaPath:"#/properties/provider/type",keyword:"type",params:{type: schema49.properties.provider.type},message:"must be string,null"}];
return false;
}
var valid0 = _errs50 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.topic !== undefined){
const _errs52 = errors;
if(typeof data.topic !== "string"){
validate33.errors = [{instancePath:instancePath+"/topic",schemaPath:"#/properties/topic/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs52 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.unread !== undefined){
let data25 = data.unread;
const _errs54 = errors;
if(!(((typeof data25 == "number") && (!(data25 % 1) && !isNaN(data25))) && (isFinite(data25)))){
validate33.errors = [{instancePath:instancePath+"/unread",schemaPath:"#/properties/unread/type",keyword:"type",params:{type: "integer"},message:"must be integer"}];
return false;
}
if(errors === _errs54){
if((typeof data25 == "number") && (isFinite(data25))){
if(data25 < 0 || isNaN(data25)){
validate33.errors = [{instancePath:instancePath+"/unread",schemaPath:"#/properties/unread/minimum",keyword:"minimum",params:{comparison: ">=", limit: 0},message:"must be >= 0"}];
return false;
}
}
}
var valid0 = _errs54 === errors;
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
else {
validate33.errors = [{instancePath,schemaPath:"#/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
validate33.errors = vErrors;
return errors === 0;
}
validate33.evaluated = {"props":{"active":true,"channelId":true,"commands":true,"id":true,"inputLimitBytes":true,"kind":true,"lastMessageId":true,"members":true,"name":true,"owner":true,"provider":true,"topic":true,"unread":true},"dynamicProps":false,"dynamicItems":false};


function validate32(data, {instancePath="", parentData, parentDataProperty, rootData=data, dynamicAnchors={}}={}){
let vErrors = null;
let errors = 0;
const evaluated0 = validate32.evaluated;
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
validate32.errors = [{instancePath,schemaPath:"#/required",keyword:"required",params:{missingProperty: missing0},message:"must have required property '"+missing0+"'"}];
return false;
}
else {
if(data.commandHistory !== undefined){
let data0 = data.commandHistory;
const _errs1 = errors;
if(errors === _errs1){
if(Array.isArray(data0)){
var valid1 = true;
const len0 = data0.length;
for(let i0=0; i0<len0; i0++){
const _errs3 = errors;
if(typeof data0[i0] !== "string"){
validate32.errors = [{instancePath:instancePath+"/commandHistory/" + i0,schemaPath:"#/properties/commandHistory/items/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid1 = _errs3 === errors;
if(!valid1){
break;
}
}
}
else {
validate32.errors = [{instancePath:instancePath+"/commandHistory",schemaPath:"#/properties/commandHistory/type",keyword:"type",params:{type: "array"},message:"must be array"}];
return false;
}
}
var valid0 = _errs1 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.conversations !== undefined){
let data2 = data.conversations;
const _errs5 = errors;
if(errors === _errs5){
if(Array.isArray(data2)){
var valid2 = true;
const len1 = data2.length;
for(let i1=0; i1<len1; i1++){
const _errs7 = errors;
if(!(validate33(data2[i1], {instancePath:instancePath+"/conversations/" + i1,parentData:data2,parentDataProperty:i1,rootData,dynamicAnchors}))){
vErrors = vErrors === null ? validate33.errors : vErrors.concat(validate33.errors);
errors = vErrors.length;
}
var valid2 = _errs7 === errors;
if(!valid2){
break;
}
}
}
else {
validate32.errors = [{instancePath:instancePath+"/conversations",schemaPath:"#/properties/conversations/type",keyword:"type",params:{type: "array"},message:"must be array"}];
return false;
}
}
var valid0 = _errs5 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.inputHistory !== undefined){
let data4 = data.inputHistory;
const _errs8 = errors;
if(errors === _errs8){
if(Array.isArray(data4)){
var valid3 = true;
const len2 = data4.length;
for(let i2=0; i2<len2; i2++){
let data5 = data4[i2];
const _errs10 = errors;
const _errs11 = errors;
if(errors === _errs11){
if(data5 && typeof data5 == "object" && !Array.isArray(data5)){
let missing1;
if((data5.text === undefined) && (missing1 = "text")){
validate32.errors = [{instancePath:instancePath+"/inputHistory/" + i2,schemaPath:"#/$defs/InputHistoryEntry/required",keyword:"required",params:{missingProperty: missing1},message:"must have required property '"+missing1+"'"}];
return false;
}
else {
if(data5.conversation !== undefined){
let data6 = data5.conversation;
const _errs13 = errors;
if((typeof data6 !== "string") && (data6 !== null)){
validate32.errors = [{instancePath:instancePath+"/inputHistory/" + i2+"/conversation",schemaPath:"#/$defs/InputHistoryEntry/properties/conversation/type",keyword:"type",params:{type: schema53.properties.conversation.type},message:"must be string,null"}];
return false;
}
var valid5 = _errs13 === errors;
}
else {
var valid5 = true;
}
if(valid5){
if(data5.text !== undefined){
const _errs15 = errors;
if(typeof data5.text !== "string"){
validate32.errors = [{instancePath:instancePath+"/inputHistory/" + i2+"/text",schemaPath:"#/$defs/InputHistoryEntry/properties/text/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid5 = _errs15 === errors;
}
else {
var valid5 = true;
}
}
}
}
else {
validate32.errors = [{instancePath:instancePath+"/inputHistory/" + i2,schemaPath:"#/$defs/InputHistoryEntry/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
var valid3 = _errs10 === errors;
if(!valid3){
break;
}
}
}
else {
validate32.errors = [{instancePath:instancePath+"/inputHistory",schemaPath:"#/properties/inputHistory/type",keyword:"type",params:{type: "array"},message:"must be array"}];
return false;
}
}
var valid0 = _errs8 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.instance !== undefined){
let data8 = data.instance;
const _errs17 = errors;
const _errs18 = errors;
if(errors === _errs18){
if(data8 && typeof data8 == "object" && !Array.isArray(data8)){
let missing2;
if((((((((((data8.id === undefined) && (missing2 = "id")) || ((data8.label === undefined) && (missing2 = "label"))) || ((data8.bootId === undefined) && (missing2 = "bootId"))) || ((data8.locked === undefined) && (missing2 = "locked"))) || ((data8.protocolLocked === undefined) && (missing2 = "protocolLocked"))) || ((data8.profileExists === undefined) && (missing2 = "profileExists"))) || ((data8.archiveExists === undefined) && (missing2 = "archiveExists"))) || ((data8.safetyNumber === undefined) && (missing2 = "safetyNumber"))) || ((data8.capabilities === undefined) && (missing2 = "capabilities"))){
validate32.errors = [{instancePath:instancePath+"/instance",schemaPath:"#/$defs/InstanceInfo/required",keyword:"required",params:{missingProperty: missing2},message:"must have required property '"+missing2+"'"}];
return false;
}
else {
if(data8.archiveExists !== undefined){
const _errs20 = errors;
if(typeof data8.archiveExists !== "boolean"){
validate32.errors = [{instancePath:instancePath+"/instance/archiveExists",schemaPath:"#/$defs/InstanceInfo/properties/archiveExists/type",keyword:"type",params:{type: "boolean"},message:"must be boolean"}];
return false;
}
var valid7 = _errs20 === errors;
}
else {
var valid7 = true;
}
if(valid7){
if(data8.bootId !== undefined){
const _errs22 = errors;
if(typeof data8.bootId !== "string"){
validate32.errors = [{instancePath:instancePath+"/instance/bootId",schemaPath:"#/$defs/InstanceInfo/properties/bootId/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid7 = _errs22 === errors;
}
else {
var valid7 = true;
}
if(valid7){
if(data8.capabilities !== undefined){
let data11 = data8.capabilities;
const _errs24 = errors;
if(errors === _errs24){
if(Array.isArray(data11)){
var valid8 = true;
const len3 = data11.length;
for(let i3=0; i3<len3; i3++){
const _errs26 = errors;
if(typeof data11[i3] !== "string"){
validate32.errors = [{instancePath:instancePath+"/instance/capabilities/" + i3,schemaPath:"#/$defs/InstanceInfo/properties/capabilities/items/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid8 = _errs26 === errors;
if(!valid8){
break;
}
}
}
else {
validate32.errors = [{instancePath:instancePath+"/instance/capabilities",schemaPath:"#/$defs/InstanceInfo/properties/capabilities/type",keyword:"type",params:{type: "array"},message:"must be array"}];
return false;
}
}
var valid7 = _errs24 === errors;
}
else {
var valid7 = true;
}
if(valid7){
if(data8.id !== undefined){
const _errs28 = errors;
if(typeof data8.id !== "string"){
validate32.errors = [{instancePath:instancePath+"/instance/id",schemaPath:"#/$defs/InstanceInfo/properties/id/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid7 = _errs28 === errors;
}
else {
var valid7 = true;
}
if(valid7){
if(data8.label !== undefined){
const _errs30 = errors;
if(typeof data8.label !== "string"){
validate32.errors = [{instancePath:instancePath+"/instance/label",schemaPath:"#/$defs/InstanceInfo/properties/label/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid7 = _errs30 === errors;
}
else {
var valid7 = true;
}
if(valid7){
if(data8.locked !== undefined){
const _errs32 = errors;
if(typeof data8.locked !== "boolean"){
validate32.errors = [{instancePath:instancePath+"/instance/locked",schemaPath:"#/$defs/InstanceInfo/properties/locked/type",keyword:"type",params:{type: "boolean"},message:"must be boolean"}];
return false;
}
var valid7 = _errs32 === errors;
}
else {
var valid7 = true;
}
if(valid7){
if(data8.profileExists !== undefined){
const _errs34 = errors;
if(typeof data8.profileExists !== "boolean"){
validate32.errors = [{instancePath:instancePath+"/instance/profileExists",schemaPath:"#/$defs/InstanceInfo/properties/profileExists/type",keyword:"type",params:{type: "boolean"},message:"must be boolean"}];
return false;
}
var valid7 = _errs34 === errors;
}
else {
var valid7 = true;
}
if(valid7){
if(data8.protocolLocked !== undefined){
const _errs36 = errors;
if(typeof data8.protocolLocked !== "boolean"){
validate32.errors = [{instancePath:instancePath+"/instance/protocolLocked",schemaPath:"#/$defs/InstanceInfo/properties/protocolLocked/type",keyword:"type",params:{type: "boolean"},message:"must be boolean"}];
return false;
}
var valid7 = _errs36 === errors;
}
else {
var valid7 = true;
}
if(valid7){
if(data8.safetyNumber !== undefined){
const _errs38 = errors;
if(typeof data8.safetyNumber !== "string"){
validate32.errors = [{instancePath:instancePath+"/instance/safetyNumber",schemaPath:"#/$defs/InstanceInfo/properties/safetyNumber/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid7 = _errs38 === errors;
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
}
}
}
}
else {
validate32.errors = [{instancePath:instancePath+"/instance",schemaPath:"#/$defs/InstanceInfo/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
var valid0 = _errs17 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.providerErrors !== undefined){
let data19 = data.providerErrors;
const _errs40 = errors;
if(errors === _errs40){
if(Array.isArray(data19)){
var valid9 = true;
const len4 = data19.length;
for(let i4=0; i4<len4; i4++){
let data20 = data19[i4];
const _errs42 = errors;
const _errs43 = errors;
if(errors === _errs43){
if(data20 && typeof data20 == "object" && !Array.isArray(data20)){
let missing3;
if(((((data20.id === undefined) && (missing3 = "id")) || ((data20.code === undefined) && (missing3 = "code"))) || ((data20.message === undefined) && (missing3 = "message"))) || ((data20.retryable === undefined) && (missing3 = "retryable"))){
validate32.errors = [{instancePath:instancePath+"/providerErrors/" + i4,schemaPath:"#/$defs/ProviderStatus/required",keyword:"required",params:{missingProperty: missing3},message:"must have required property '"+missing3+"'"}];
return false;
}
else {
if(data20.code !== undefined){
const _errs45 = errors;
if(typeof data20.code !== "string"){
validate32.errors = [{instancePath:instancePath+"/providerErrors/" + i4+"/code",schemaPath:"#/$defs/ProviderStatus/properties/code/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid11 = _errs45 === errors;
}
else {
var valid11 = true;
}
if(valid11){
if(data20.id !== undefined){
const _errs47 = errors;
if(typeof data20.id !== "string"){
validate32.errors = [{instancePath:instancePath+"/providerErrors/" + i4+"/id",schemaPath:"#/$defs/ProviderStatus/properties/id/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid11 = _errs47 === errors;
}
else {
var valid11 = true;
}
if(valid11){
if(data20.message !== undefined){
const _errs49 = errors;
if(typeof data20.message !== "string"){
validate32.errors = [{instancePath:instancePath+"/providerErrors/" + i4+"/message",schemaPath:"#/$defs/ProviderStatus/properties/message/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid11 = _errs49 === errors;
}
else {
var valid11 = true;
}
if(valid11){
if(data20.retryable !== undefined){
const _errs51 = errors;
if(typeof data20.retryable !== "boolean"){
validate32.errors = [{instancePath:instancePath+"/providerErrors/" + i4+"/retryable",schemaPath:"#/$defs/ProviderStatus/properties/retryable/type",keyword:"type",params:{type: "boolean"},message:"must be boolean"}];
return false;
}
var valid11 = _errs51 === errors;
}
else {
var valid11 = true;
}
}
}
}
}
}
else {
validate32.errors = [{instancePath:instancePath+"/providerErrors/" + i4,schemaPath:"#/$defs/ProviderStatus/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
var valid9 = _errs42 === errors;
if(!valid9){
break;
}
}
}
else {
validate32.errors = [{instancePath:instancePath+"/providerErrors",schemaPath:"#/properties/providerErrors/type",keyword:"type",params:{type: "array"},message:"must be array"}];
return false;
}
}
var valid0 = _errs40 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.revision !== undefined){
const _errs53 = errors;
if(typeof data.revision !== "string"){
validate32.errors = [{instancePath:instancePath+"/revision",schemaPath:"#/properties/revision/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs53 === errors;
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
else {
validate32.errors = [{instancePath,schemaPath:"#/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
validate32.errors = vErrors;
return errors === 0;
}
validate32.evaluated = {"props":{"commandHistory":true,"conversations":true,"inputHistory":true,"instance":true,"providerErrors":true,"revision":true},"dynamicProps":false,"dynamicItems":false};

export const disconnect_error = validate35;
const schema56 = {"$schema":"https://json-schema.org/draft/2020-12/schema","additionalProperties":false,"properties":{"code":{"type":"string"},"message":{"type":"string"}},"required":["code","message"],"title":"ChatError","type":"object"};

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
if(((data.code === undefined) && (missing0 = "code")) || ((data.message === undefined) && (missing0 = "message"))){
validate35.errors = [{instancePath,schemaPath:"#/required",keyword:"required",params:{missingProperty: missing0},message:"must have required property '"+missing0+"'"}];
return false;
}
else {
const _errs1 = errors;
for(const key0 in data){
if(!((key0 === "code") || (key0 === "message"))){
validate35.errors = [{instancePath,schemaPath:"#/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key0},message:"must NOT have additional properties"}];
return false;
break;
}
}
if(_errs1 === errors){
if(data.code !== undefined){
const _errs2 = errors;
if(typeof data.code !== "string"){
validate35.errors = [{instancePath:instancePath+"/code",schemaPath:"#/properties/code/type",keyword:"type",params:{type: "string"},message:"must be string"}];
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
validate35.errors = [{instancePath:instancePath+"/message",schemaPath:"#/properties/message/type",keyword:"type",params:{type: "string"},message:"must be string"}];
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
validate35.errors = [{instancePath,schemaPath:"#/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
validate35.errors = vErrors;
return errors === 0;
}
validate35.evaluated = {"props":true,"dynamicProps":false,"dynamicItems":false};

export const snapshot_args = validate36;
const schema57 = {"$schema":"https://json-schema.org/draft/2020-12/schema","additionalProperties":false,"title":"ChatSnapshotArgs","type":"object"};

function validate36(data, {instancePath="", parentData, parentDataProperty, rootData=data, dynamicAnchors={}}={}){
let vErrors = null;
let errors = 0;
const evaluated0 = validate36.evaluated;
if(evaluated0.dynamicProps){
evaluated0.props = undefined;
}
if(evaluated0.dynamicItems){
evaluated0.items = undefined;
}
if(errors === 0){
if(data && typeof data == "object" && !Array.isArray(data)){
for(const key0 in data){
validate36.errors = [{instancePath,schemaPath:"#/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key0},message:"must NOT have additional properties"}];
return false;
break;
}
}
else {
validate36.errors = [{instancePath,schemaPath:"#/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
validate36.errors = vErrors;
return errors === 0;
}
validate36.evaluated = {"props":true,"dynamicProps":false,"dynamicItems":false};

export const snapshot_output = validate37;
const schema58 = {"$defs":{"CommandSpec":{"properties":{"available":{"type":"boolean"},"capability":{"type":["string","null"]},"description":{"type":"string"},"name":{"type":"string"},"scope":{"type":"string"},"usage":{"type":"string"}},"required":["name","usage","description","scope","available"],"type":"object"},"Conversation":{"properties":{"active":{"type":"boolean"},"channelId":{"type":"string"},"commands":{"default":[],"items":{"$ref":"#/$defs/CommandSpec"},"type":"array"},"id":{"type":"string"},"inputLimitBytes":{"default":12000,"format":"uint","minimum":0,"type":"integer"},"kind":{"$ref":"#/$defs/ConversationKind"},"lastMessageId":{"type":["string","null"]},"members":{"items":{"$ref":"#/$defs/Member"},"type":"array"},"name":{"type":"string"},"owner":{"type":"boolean"},"provider":{"default":null,"type":["string","null"]},"topic":{"type":"string"},"unread":{"format":"uint32","minimum":0,"type":"integer"}},"required":["id","channelId","kind","name","topic","active","owner","members","unread"],"type":"object"},"ConversationKind":{"enum":["channel","query","archive"],"type":"string"},"InputHistoryEntry":{"properties":{"conversation":{"type":["string","null"]},"text":{"type":"string"}},"required":["text"],"type":"object"},"InstanceInfo":{"properties":{"archiveExists":{"type":"boolean"},"bootId":{"type":"string"},"capabilities":{"items":{"type":"string"},"type":"array"},"id":{"type":"string"},"label":{"type":"string"},"locked":{"type":"boolean"},"profileExists":{"type":"boolean"},"protocolLocked":{"type":"boolean"},"safetyNumber":{"type":"string"}},"required":["id","label","bootId","locked","protocolLocked","profileExists","archiveExists","safetyNumber","capabilities"],"type":"object"},"Member":{"properties":{"capabilities":{"default":[],"items":{"type":"string"},"type":"array"},"id":{"type":"string"},"isSelf":{"type":"boolean"},"nickname":{"type":"string"}},"required":["id","nickname","isSelf"],"type":"object"},"ProviderStatus":{"properties":{"code":{"type":"string"},"id":{"type":"string"},"message":{"type":"string"},"retryable":{"type":"boolean"}},"required":["id","code","message","retryable"],"type":"object"}},"$schema":"https://json-schema.org/draft/2020-12/schema","properties":{"commandHistory":{"items":{"type":"string"},"type":"array"},"conversations":{"items":{"$ref":"#/$defs/Conversation"},"type":"array"},"inputHistory":{"items":{"$ref":"#/$defs/InputHistoryEntry"},"type":"array"},"instance":{"$ref":"#/$defs/InstanceInfo"},"providerErrors":{"default":[],"items":{"$ref":"#/$defs/ProviderStatus"},"type":"array"},"revision":{"type":"string"}},"required":["instance","revision","conversations","commandHistory","inputHistory"],"title":"Snapshot","type":"object"};
const schema63 = {"properties":{"conversation":{"type":["string","null"]},"text":{"type":"string"}},"required":["text"],"type":"object"};
const schema64 = {"properties":{"archiveExists":{"type":"boolean"},"bootId":{"type":"string"},"capabilities":{"items":{"type":"string"},"type":"array"},"id":{"type":"string"},"label":{"type":"string"},"locked":{"type":"boolean"},"profileExists":{"type":"boolean"},"protocolLocked":{"type":"boolean"},"safetyNumber":{"type":"string"}},"required":["id","label","bootId","locked","protocolLocked","profileExists","archiveExists","safetyNumber","capabilities"],"type":"object"};
const schema65 = {"properties":{"code":{"type":"string"},"id":{"type":"string"},"message":{"type":"string"},"retryable":{"type":"boolean"}},"required":["id","code","message","retryable"],"type":"object"};
const schema59 = {"properties":{"active":{"type":"boolean"},"channelId":{"type":"string"},"commands":{"default":[],"items":{"$ref":"#/$defs/CommandSpec"},"type":"array"},"id":{"type":"string"},"inputLimitBytes":{"default":12000,"format":"uint","minimum":0,"type":"integer"},"kind":{"$ref":"#/$defs/ConversationKind"},"lastMessageId":{"type":["string","null"]},"members":{"items":{"$ref":"#/$defs/Member"},"type":"array"},"name":{"type":"string"},"owner":{"type":"boolean"},"provider":{"default":null,"type":["string","null"]},"topic":{"type":"string"},"unread":{"format":"uint32","minimum":0,"type":"integer"}},"required":["id","channelId","kind","name","topic","active","owner","members","unread"],"type":"object"};
const schema60 = {"properties":{"available":{"type":"boolean"},"capability":{"type":["string","null"]},"description":{"type":"string"},"name":{"type":"string"},"scope":{"type":"string"},"usage":{"type":"string"}},"required":["name","usage","description","scope","available"],"type":"object"};
const schema61 = {"enum":["channel","query","archive"],"type":"string"};
const schema62 = {"properties":{"capabilities":{"default":[],"items":{"type":"string"},"type":"array"},"id":{"type":"string"},"isSelf":{"type":"boolean"},"nickname":{"type":"string"}},"required":["id","nickname","isSelf"],"type":"object"};

function validate38(data, {instancePath="", parentData, parentDataProperty, rootData=data, dynamicAnchors={}}={}){
let vErrors = null;
let errors = 0;
const evaluated0 = validate38.evaluated;
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
validate38.errors = [{instancePath,schemaPath:"#/required",keyword:"required",params:{missingProperty: missing0},message:"must have required property '"+missing0+"'"}];
return false;
}
else {
if(data.active !== undefined){
const _errs1 = errors;
if(typeof data.active !== "boolean"){
validate38.errors = [{instancePath:instancePath+"/active",schemaPath:"#/properties/active/type",keyword:"type",params:{type: "boolean"},message:"must be boolean"}];
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
validate38.errors = [{instancePath:instancePath+"/channelId",schemaPath:"#/properties/channelId/type",keyword:"type",params:{type: "string"},message:"must be string"}];
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
validate38.errors = [{instancePath:instancePath+"/commands/" + i0,schemaPath:"#/$defs/CommandSpec/required",keyword:"required",params:{missingProperty: missing1},message:"must have required property '"+missing1+"'"}];
return false;
}
else {
if(data3.available !== undefined){
const _errs10 = errors;
if(typeof data3.available !== "boolean"){
validate38.errors = [{instancePath:instancePath+"/commands/" + i0+"/available",schemaPath:"#/$defs/CommandSpec/properties/available/type",keyword:"type",params:{type: "boolean"},message:"must be boolean"}];
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
validate38.errors = [{instancePath:instancePath+"/commands/" + i0+"/capability",schemaPath:"#/$defs/CommandSpec/properties/capability/type",keyword:"type",params:{type: schema60.properties.capability.type},message:"must be string,null"}];
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
validate38.errors = [{instancePath:instancePath+"/commands/" + i0+"/description",schemaPath:"#/$defs/CommandSpec/properties/description/type",keyword:"type",params:{type: "string"},message:"must be string"}];
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
validate38.errors = [{instancePath:instancePath+"/commands/" + i0+"/name",schemaPath:"#/$defs/CommandSpec/properties/name/type",keyword:"type",params:{type: "string"},message:"must be string"}];
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
validate38.errors = [{instancePath:instancePath+"/commands/" + i0+"/scope",schemaPath:"#/$defs/CommandSpec/properties/scope/type",keyword:"type",params:{type: "string"},message:"must be string"}];
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
validate38.errors = [{instancePath:instancePath+"/commands/" + i0+"/usage",schemaPath:"#/$defs/CommandSpec/properties/usage/type",keyword:"type",params:{type: "string"},message:"must be string"}];
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
validate38.errors = [{instancePath:instancePath+"/commands/" + i0,schemaPath:"#/$defs/CommandSpec/type",keyword:"type",params:{type: "object"},message:"must be object"}];
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
validate38.errors = [{instancePath:instancePath+"/commands",schemaPath:"#/properties/commands/type",keyword:"type",params:{type: "array"},message:"must be array"}];
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
const _errs22 = errors;
if(typeof data.id !== "string"){
validate38.errors = [{instancePath:instancePath+"/id",schemaPath:"#/properties/id/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs22 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.inputLimitBytes !== undefined){
let data11 = data.inputLimitBytes;
const _errs24 = errors;
if(!(((typeof data11 == "number") && (!(data11 % 1) && !isNaN(data11))) && (isFinite(data11)))){
validate38.errors = [{instancePath:instancePath+"/inputLimitBytes",schemaPath:"#/properties/inputLimitBytes/type",keyword:"type",params:{type: "integer"},message:"must be integer"}];
return false;
}
if(errors === _errs24){
if((typeof data11 == "number") && (isFinite(data11))){
if(data11 < 0 || isNaN(data11)){
validate38.errors = [{instancePath:instancePath+"/inputLimitBytes",schemaPath:"#/properties/inputLimitBytes/minimum",keyword:"minimum",params:{comparison: ">=", limit: 0},message:"must be >= 0"}];
return false;
}
}
}
var valid0 = _errs24 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.kind !== undefined){
let data12 = data.kind;
const _errs26 = errors;
if(typeof data12 !== "string"){
validate38.errors = [{instancePath:instancePath+"/kind",schemaPath:"#/$defs/ConversationKind/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
if(!(((data12 === "channel") || (data12 === "query")) || (data12 === "archive"))){
validate38.errors = [{instancePath:instancePath+"/kind",schemaPath:"#/$defs/ConversationKind/enum",keyword:"enum",params:{allowedValues: schema61.enum},message:"must be equal to one of the allowed values"}];
return false;
}
var valid0 = _errs26 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.lastMessageId !== undefined){
let data13 = data.lastMessageId;
const _errs29 = errors;
if((typeof data13 !== "string") && (data13 !== null)){
validate38.errors = [{instancePath:instancePath+"/lastMessageId",schemaPath:"#/properties/lastMessageId/type",keyword:"type",params:{type: schema59.properties.lastMessageId.type},message:"must be string,null"}];
return false;
}
var valid0 = _errs29 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.members !== undefined){
let data14 = data.members;
const _errs31 = errors;
if(errors === _errs31){
if(Array.isArray(data14)){
var valid5 = true;
const len1 = data14.length;
for(let i1=0; i1<len1; i1++){
let data15 = data14[i1];
const _errs33 = errors;
const _errs34 = errors;
if(errors === _errs34){
if(data15 && typeof data15 == "object" && !Array.isArray(data15)){
let missing2;
if((((data15.id === undefined) && (missing2 = "id")) || ((data15.nickname === undefined) && (missing2 = "nickname"))) || ((data15.isSelf === undefined) && (missing2 = "isSelf"))){
validate38.errors = [{instancePath:instancePath+"/members/" + i1,schemaPath:"#/$defs/Member/required",keyword:"required",params:{missingProperty: missing2},message:"must have required property '"+missing2+"'"}];
return false;
}
else {
if(data15.capabilities !== undefined){
let data16 = data15.capabilities;
const _errs36 = errors;
if(errors === _errs36){
if(Array.isArray(data16)){
var valid8 = true;
const len2 = data16.length;
for(let i2=0; i2<len2; i2++){
const _errs38 = errors;
if(typeof data16[i2] !== "string"){
validate38.errors = [{instancePath:instancePath+"/members/" + i1+"/capabilities/" + i2,schemaPath:"#/$defs/Member/properties/capabilities/items/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid8 = _errs38 === errors;
if(!valid8){
break;
}
}
}
else {
validate38.errors = [{instancePath:instancePath+"/members/" + i1+"/capabilities",schemaPath:"#/$defs/Member/properties/capabilities/type",keyword:"type",params:{type: "array"},message:"must be array"}];
return false;
}
}
var valid7 = _errs36 === errors;
}
else {
var valid7 = true;
}
if(valid7){
if(data15.id !== undefined){
const _errs40 = errors;
if(typeof data15.id !== "string"){
validate38.errors = [{instancePath:instancePath+"/members/" + i1+"/id",schemaPath:"#/$defs/Member/properties/id/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid7 = _errs40 === errors;
}
else {
var valid7 = true;
}
if(valid7){
if(data15.isSelf !== undefined){
const _errs42 = errors;
if(typeof data15.isSelf !== "boolean"){
validate38.errors = [{instancePath:instancePath+"/members/" + i1+"/isSelf",schemaPath:"#/$defs/Member/properties/isSelf/type",keyword:"type",params:{type: "boolean"},message:"must be boolean"}];
return false;
}
var valid7 = _errs42 === errors;
}
else {
var valid7 = true;
}
if(valid7){
if(data15.nickname !== undefined){
const _errs44 = errors;
if(typeof data15.nickname !== "string"){
validate38.errors = [{instancePath:instancePath+"/members/" + i1+"/nickname",schemaPath:"#/$defs/Member/properties/nickname/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
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
}
else {
validate38.errors = [{instancePath:instancePath+"/members/" + i1,schemaPath:"#/$defs/Member/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
var valid5 = _errs33 === errors;
if(!valid5){
break;
}
}
}
else {
validate38.errors = [{instancePath:instancePath+"/members",schemaPath:"#/properties/members/type",keyword:"type",params:{type: "array"},message:"must be array"}];
return false;
}
}
var valid0 = _errs31 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.name !== undefined){
const _errs46 = errors;
if(typeof data.name !== "string"){
validate38.errors = [{instancePath:instancePath+"/name",schemaPath:"#/properties/name/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs46 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.owner !== undefined){
const _errs48 = errors;
if(typeof data.owner !== "boolean"){
validate38.errors = [{instancePath:instancePath+"/owner",schemaPath:"#/properties/owner/type",keyword:"type",params:{type: "boolean"},message:"must be boolean"}];
return false;
}
var valid0 = _errs48 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.provider !== undefined){
let data23 = data.provider;
const _errs50 = errors;
if((typeof data23 !== "string") && (data23 !== null)){
validate38.errors = [{instancePath:instancePath+"/provider",schemaPath:"#/properties/provider/type",keyword:"type",params:{type: schema59.properties.provider.type},message:"must be string,null"}];
return false;
}
var valid0 = _errs50 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.topic !== undefined){
const _errs52 = errors;
if(typeof data.topic !== "string"){
validate38.errors = [{instancePath:instancePath+"/topic",schemaPath:"#/properties/topic/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs52 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.unread !== undefined){
let data25 = data.unread;
const _errs54 = errors;
if(!(((typeof data25 == "number") && (!(data25 % 1) && !isNaN(data25))) && (isFinite(data25)))){
validate38.errors = [{instancePath:instancePath+"/unread",schemaPath:"#/properties/unread/type",keyword:"type",params:{type: "integer"},message:"must be integer"}];
return false;
}
if(errors === _errs54){
if((typeof data25 == "number") && (isFinite(data25))){
if(data25 < 0 || isNaN(data25)){
validate38.errors = [{instancePath:instancePath+"/unread",schemaPath:"#/properties/unread/minimum",keyword:"minimum",params:{comparison: ">=", limit: 0},message:"must be >= 0"}];
return false;
}
}
}
var valid0 = _errs54 === errors;
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
else {
validate38.errors = [{instancePath,schemaPath:"#/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
validate38.errors = vErrors;
return errors === 0;
}
validate38.evaluated = {"props":{"active":true,"channelId":true,"commands":true,"id":true,"inputLimitBytes":true,"kind":true,"lastMessageId":true,"members":true,"name":true,"owner":true,"provider":true,"topic":true,"unread":true},"dynamicProps":false,"dynamicItems":false};


function validate37(data, {instancePath="", parentData, parentDataProperty, rootData=data, dynamicAnchors={}}={}){
let vErrors = null;
let errors = 0;
const evaluated0 = validate37.evaluated;
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
validate37.errors = [{instancePath,schemaPath:"#/required",keyword:"required",params:{missingProperty: missing0},message:"must have required property '"+missing0+"'"}];
return false;
}
else {
if(data.commandHistory !== undefined){
let data0 = data.commandHistory;
const _errs1 = errors;
if(errors === _errs1){
if(Array.isArray(data0)){
var valid1 = true;
const len0 = data0.length;
for(let i0=0; i0<len0; i0++){
const _errs3 = errors;
if(typeof data0[i0] !== "string"){
validate37.errors = [{instancePath:instancePath+"/commandHistory/" + i0,schemaPath:"#/properties/commandHistory/items/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid1 = _errs3 === errors;
if(!valid1){
break;
}
}
}
else {
validate37.errors = [{instancePath:instancePath+"/commandHistory",schemaPath:"#/properties/commandHistory/type",keyword:"type",params:{type: "array"},message:"must be array"}];
return false;
}
}
var valid0 = _errs1 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.conversations !== undefined){
let data2 = data.conversations;
const _errs5 = errors;
if(errors === _errs5){
if(Array.isArray(data2)){
var valid2 = true;
const len1 = data2.length;
for(let i1=0; i1<len1; i1++){
const _errs7 = errors;
if(!(validate38(data2[i1], {instancePath:instancePath+"/conversations/" + i1,parentData:data2,parentDataProperty:i1,rootData,dynamicAnchors}))){
vErrors = vErrors === null ? validate38.errors : vErrors.concat(validate38.errors);
errors = vErrors.length;
}
var valid2 = _errs7 === errors;
if(!valid2){
break;
}
}
}
else {
validate37.errors = [{instancePath:instancePath+"/conversations",schemaPath:"#/properties/conversations/type",keyword:"type",params:{type: "array"},message:"must be array"}];
return false;
}
}
var valid0 = _errs5 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.inputHistory !== undefined){
let data4 = data.inputHistory;
const _errs8 = errors;
if(errors === _errs8){
if(Array.isArray(data4)){
var valid3 = true;
const len2 = data4.length;
for(let i2=0; i2<len2; i2++){
let data5 = data4[i2];
const _errs10 = errors;
const _errs11 = errors;
if(errors === _errs11){
if(data5 && typeof data5 == "object" && !Array.isArray(data5)){
let missing1;
if((data5.text === undefined) && (missing1 = "text")){
validate37.errors = [{instancePath:instancePath+"/inputHistory/" + i2,schemaPath:"#/$defs/InputHistoryEntry/required",keyword:"required",params:{missingProperty: missing1},message:"must have required property '"+missing1+"'"}];
return false;
}
else {
if(data5.conversation !== undefined){
let data6 = data5.conversation;
const _errs13 = errors;
if((typeof data6 !== "string") && (data6 !== null)){
validate37.errors = [{instancePath:instancePath+"/inputHistory/" + i2+"/conversation",schemaPath:"#/$defs/InputHistoryEntry/properties/conversation/type",keyword:"type",params:{type: schema63.properties.conversation.type},message:"must be string,null"}];
return false;
}
var valid5 = _errs13 === errors;
}
else {
var valid5 = true;
}
if(valid5){
if(data5.text !== undefined){
const _errs15 = errors;
if(typeof data5.text !== "string"){
validate37.errors = [{instancePath:instancePath+"/inputHistory/" + i2+"/text",schemaPath:"#/$defs/InputHistoryEntry/properties/text/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid5 = _errs15 === errors;
}
else {
var valid5 = true;
}
}
}
}
else {
validate37.errors = [{instancePath:instancePath+"/inputHistory/" + i2,schemaPath:"#/$defs/InputHistoryEntry/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
var valid3 = _errs10 === errors;
if(!valid3){
break;
}
}
}
else {
validate37.errors = [{instancePath:instancePath+"/inputHistory",schemaPath:"#/properties/inputHistory/type",keyword:"type",params:{type: "array"},message:"must be array"}];
return false;
}
}
var valid0 = _errs8 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.instance !== undefined){
let data8 = data.instance;
const _errs17 = errors;
const _errs18 = errors;
if(errors === _errs18){
if(data8 && typeof data8 == "object" && !Array.isArray(data8)){
let missing2;
if((((((((((data8.id === undefined) && (missing2 = "id")) || ((data8.label === undefined) && (missing2 = "label"))) || ((data8.bootId === undefined) && (missing2 = "bootId"))) || ((data8.locked === undefined) && (missing2 = "locked"))) || ((data8.protocolLocked === undefined) && (missing2 = "protocolLocked"))) || ((data8.profileExists === undefined) && (missing2 = "profileExists"))) || ((data8.archiveExists === undefined) && (missing2 = "archiveExists"))) || ((data8.safetyNumber === undefined) && (missing2 = "safetyNumber"))) || ((data8.capabilities === undefined) && (missing2 = "capabilities"))){
validate37.errors = [{instancePath:instancePath+"/instance",schemaPath:"#/$defs/InstanceInfo/required",keyword:"required",params:{missingProperty: missing2},message:"must have required property '"+missing2+"'"}];
return false;
}
else {
if(data8.archiveExists !== undefined){
const _errs20 = errors;
if(typeof data8.archiveExists !== "boolean"){
validate37.errors = [{instancePath:instancePath+"/instance/archiveExists",schemaPath:"#/$defs/InstanceInfo/properties/archiveExists/type",keyword:"type",params:{type: "boolean"},message:"must be boolean"}];
return false;
}
var valid7 = _errs20 === errors;
}
else {
var valid7 = true;
}
if(valid7){
if(data8.bootId !== undefined){
const _errs22 = errors;
if(typeof data8.bootId !== "string"){
validate37.errors = [{instancePath:instancePath+"/instance/bootId",schemaPath:"#/$defs/InstanceInfo/properties/bootId/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid7 = _errs22 === errors;
}
else {
var valid7 = true;
}
if(valid7){
if(data8.capabilities !== undefined){
let data11 = data8.capabilities;
const _errs24 = errors;
if(errors === _errs24){
if(Array.isArray(data11)){
var valid8 = true;
const len3 = data11.length;
for(let i3=0; i3<len3; i3++){
const _errs26 = errors;
if(typeof data11[i3] !== "string"){
validate37.errors = [{instancePath:instancePath+"/instance/capabilities/" + i3,schemaPath:"#/$defs/InstanceInfo/properties/capabilities/items/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid8 = _errs26 === errors;
if(!valid8){
break;
}
}
}
else {
validate37.errors = [{instancePath:instancePath+"/instance/capabilities",schemaPath:"#/$defs/InstanceInfo/properties/capabilities/type",keyword:"type",params:{type: "array"},message:"must be array"}];
return false;
}
}
var valid7 = _errs24 === errors;
}
else {
var valid7 = true;
}
if(valid7){
if(data8.id !== undefined){
const _errs28 = errors;
if(typeof data8.id !== "string"){
validate37.errors = [{instancePath:instancePath+"/instance/id",schemaPath:"#/$defs/InstanceInfo/properties/id/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid7 = _errs28 === errors;
}
else {
var valid7 = true;
}
if(valid7){
if(data8.label !== undefined){
const _errs30 = errors;
if(typeof data8.label !== "string"){
validate37.errors = [{instancePath:instancePath+"/instance/label",schemaPath:"#/$defs/InstanceInfo/properties/label/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid7 = _errs30 === errors;
}
else {
var valid7 = true;
}
if(valid7){
if(data8.locked !== undefined){
const _errs32 = errors;
if(typeof data8.locked !== "boolean"){
validate37.errors = [{instancePath:instancePath+"/instance/locked",schemaPath:"#/$defs/InstanceInfo/properties/locked/type",keyword:"type",params:{type: "boolean"},message:"must be boolean"}];
return false;
}
var valid7 = _errs32 === errors;
}
else {
var valid7 = true;
}
if(valid7){
if(data8.profileExists !== undefined){
const _errs34 = errors;
if(typeof data8.profileExists !== "boolean"){
validate37.errors = [{instancePath:instancePath+"/instance/profileExists",schemaPath:"#/$defs/InstanceInfo/properties/profileExists/type",keyword:"type",params:{type: "boolean"},message:"must be boolean"}];
return false;
}
var valid7 = _errs34 === errors;
}
else {
var valid7 = true;
}
if(valid7){
if(data8.protocolLocked !== undefined){
const _errs36 = errors;
if(typeof data8.protocolLocked !== "boolean"){
validate37.errors = [{instancePath:instancePath+"/instance/protocolLocked",schemaPath:"#/$defs/InstanceInfo/properties/protocolLocked/type",keyword:"type",params:{type: "boolean"},message:"must be boolean"}];
return false;
}
var valid7 = _errs36 === errors;
}
else {
var valid7 = true;
}
if(valid7){
if(data8.safetyNumber !== undefined){
const _errs38 = errors;
if(typeof data8.safetyNumber !== "string"){
validate37.errors = [{instancePath:instancePath+"/instance/safetyNumber",schemaPath:"#/$defs/InstanceInfo/properties/safetyNumber/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid7 = _errs38 === errors;
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
}
}
}
}
else {
validate37.errors = [{instancePath:instancePath+"/instance",schemaPath:"#/$defs/InstanceInfo/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
var valid0 = _errs17 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.providerErrors !== undefined){
let data19 = data.providerErrors;
const _errs40 = errors;
if(errors === _errs40){
if(Array.isArray(data19)){
var valid9 = true;
const len4 = data19.length;
for(let i4=0; i4<len4; i4++){
let data20 = data19[i4];
const _errs42 = errors;
const _errs43 = errors;
if(errors === _errs43){
if(data20 && typeof data20 == "object" && !Array.isArray(data20)){
let missing3;
if(((((data20.id === undefined) && (missing3 = "id")) || ((data20.code === undefined) && (missing3 = "code"))) || ((data20.message === undefined) && (missing3 = "message"))) || ((data20.retryable === undefined) && (missing3 = "retryable"))){
validate37.errors = [{instancePath:instancePath+"/providerErrors/" + i4,schemaPath:"#/$defs/ProviderStatus/required",keyword:"required",params:{missingProperty: missing3},message:"must have required property '"+missing3+"'"}];
return false;
}
else {
if(data20.code !== undefined){
const _errs45 = errors;
if(typeof data20.code !== "string"){
validate37.errors = [{instancePath:instancePath+"/providerErrors/" + i4+"/code",schemaPath:"#/$defs/ProviderStatus/properties/code/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid11 = _errs45 === errors;
}
else {
var valid11 = true;
}
if(valid11){
if(data20.id !== undefined){
const _errs47 = errors;
if(typeof data20.id !== "string"){
validate37.errors = [{instancePath:instancePath+"/providerErrors/" + i4+"/id",schemaPath:"#/$defs/ProviderStatus/properties/id/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid11 = _errs47 === errors;
}
else {
var valid11 = true;
}
if(valid11){
if(data20.message !== undefined){
const _errs49 = errors;
if(typeof data20.message !== "string"){
validate37.errors = [{instancePath:instancePath+"/providerErrors/" + i4+"/message",schemaPath:"#/$defs/ProviderStatus/properties/message/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid11 = _errs49 === errors;
}
else {
var valid11 = true;
}
if(valid11){
if(data20.retryable !== undefined){
const _errs51 = errors;
if(typeof data20.retryable !== "boolean"){
validate37.errors = [{instancePath:instancePath+"/providerErrors/" + i4+"/retryable",schemaPath:"#/$defs/ProviderStatus/properties/retryable/type",keyword:"type",params:{type: "boolean"},message:"must be boolean"}];
return false;
}
var valid11 = _errs51 === errors;
}
else {
var valid11 = true;
}
}
}
}
}
}
else {
validate37.errors = [{instancePath:instancePath+"/providerErrors/" + i4,schemaPath:"#/$defs/ProviderStatus/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
var valid9 = _errs42 === errors;
if(!valid9){
break;
}
}
}
else {
validate37.errors = [{instancePath:instancePath+"/providerErrors",schemaPath:"#/properties/providerErrors/type",keyword:"type",params:{type: "array"},message:"must be array"}];
return false;
}
}
var valid0 = _errs40 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.revision !== undefined){
const _errs53 = errors;
if(typeof data.revision !== "string"){
validate37.errors = [{instancePath:instancePath+"/revision",schemaPath:"#/properties/revision/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs53 === errors;
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
else {
validate37.errors = [{instancePath,schemaPath:"#/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
validate37.errors = vErrors;
return errors === 0;
}
validate37.evaluated = {"props":{"commandHistory":true,"conversations":true,"inputHistory":true,"instance":true,"providerErrors":true,"revision":true},"dynamicProps":false,"dynamicItems":false};

export const snapshot_error = validate40;
const schema66 = {"$schema":"https://json-schema.org/draft/2020-12/schema","additionalProperties":false,"properties":{"code":{"type":"string"},"message":{"type":"string"}},"required":["code","message"],"title":"ChatError","type":"object"};

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
if(((data.code === undefined) && (missing0 = "code")) || ((data.message === undefined) && (missing0 = "message"))){
validate40.errors = [{instancePath,schemaPath:"#/required",keyword:"required",params:{missingProperty: missing0},message:"must have required property '"+missing0+"'"}];
return false;
}
else {
const _errs1 = errors;
for(const key0 in data){
if(!((key0 === "code") || (key0 === "message"))){
validate40.errors = [{instancePath,schemaPath:"#/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key0},message:"must NOT have additional properties"}];
return false;
break;
}
}
if(_errs1 === errors){
if(data.code !== undefined){
const _errs2 = errors;
if(typeof data.code !== "string"){
validate40.errors = [{instancePath:instancePath+"/code",schemaPath:"#/properties/code/type",keyword:"type",params:{type: "string"},message:"must be string"}];
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
validate40.errors = [{instancePath:instancePath+"/message",schemaPath:"#/properties/message/type",keyword:"type",params:{type: "string"},message:"must be string"}];
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
validate40.errors = [{instancePath,schemaPath:"#/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
validate40.errors = vErrors;
return errors === 0;
}
validate40.evaluated = {"props":true,"dynamicProps":false,"dynamicItems":false};

export const catalogue_args = validate41;
const schema67 = {"$schema":"https://json-schema.org/draft/2020-12/schema","additionalProperties":false,"properties":{"conversation":{"type":["string","null"]}},"title":"ChatCatalogueArgs","type":"object"};

function validate41(data, {instancePath="", parentData, parentDataProperty, rootData=data, dynamicAnchors={}}={}){
let vErrors = null;
let errors = 0;
const evaluated0 = validate41.evaluated;
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
validate41.errors = [{instancePath,schemaPath:"#/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key0},message:"must NOT have additional properties"}];
return false;
break;
}
}
if(_errs1 === errors){
if(data.conversation !== undefined){
let data0 = data.conversation;
if((typeof data0 !== "string") && (data0 !== null)){
validate41.errors = [{instancePath:instancePath+"/conversation",schemaPath:"#/properties/conversation/type",keyword:"type",params:{type: schema67.properties.conversation.type},message:"must be string,null"}];
return false;
}
}
}
}
else {
validate41.errors = [{instancePath,schemaPath:"#/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
validate41.errors = vErrors;
return errors === 0;
}
validate41.evaluated = {"props":true,"dynamicProps":false,"dynamicItems":false};

export const catalogue_output = validate42;
const schema68 = {"$defs":{"CommandSpec":{"properties":{"available":{"type":"boolean"},"capability":{"type":["string","null"]},"description":{"type":"string"},"name":{"type":"string"},"scope":{"type":"string"},"usage":{"type":"string"}},"required":["name","usage","description","scope","available"],"type":"object"}},"$schema":"https://json-schema.org/draft/2020-12/schema","items":{"$ref":"#/$defs/CommandSpec"},"title":"Array_of_CommandSpec","type":"array"};
const schema69 = {"properties":{"available":{"type":"boolean"},"capability":{"type":["string","null"]},"description":{"type":"string"},"name":{"type":"string"},"scope":{"type":"string"},"usage":{"type":"string"}},"required":["name","usage","description","scope","available"],"type":"object"};

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
validate42.errors = [{instancePath:instancePath+"/" + i0,schemaPath:"#/$defs/CommandSpec/required",keyword:"required",params:{missingProperty: missing0},message:"must have required property '"+missing0+"'"}];
return false;
}
else {
if(data0.available !== undefined){
const _errs4 = errors;
if(typeof data0.available !== "boolean"){
validate42.errors = [{instancePath:instancePath+"/" + i0+"/available",schemaPath:"#/$defs/CommandSpec/properties/available/type",keyword:"type",params:{type: "boolean"},message:"must be boolean"}];
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
validate42.errors = [{instancePath:instancePath+"/" + i0+"/capability",schemaPath:"#/$defs/CommandSpec/properties/capability/type",keyword:"type",params:{type: schema69.properties.capability.type},message:"must be string,null"}];
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
validate42.errors = [{instancePath:instancePath+"/" + i0+"/description",schemaPath:"#/$defs/CommandSpec/properties/description/type",keyword:"type",params:{type: "string"},message:"must be string"}];
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
validate42.errors = [{instancePath:instancePath+"/" + i0+"/name",schemaPath:"#/$defs/CommandSpec/properties/name/type",keyword:"type",params:{type: "string"},message:"must be string"}];
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
validate42.errors = [{instancePath:instancePath+"/" + i0+"/scope",schemaPath:"#/$defs/CommandSpec/properties/scope/type",keyword:"type",params:{type: "string"},message:"must be string"}];
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
validate42.errors = [{instancePath:instancePath+"/" + i0+"/usage",schemaPath:"#/$defs/CommandSpec/properties/usage/type",keyword:"type",params:{type: "string"},message:"must be string"}];
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
validate42.errors = [{instancePath:instancePath+"/" + i0,schemaPath:"#/$defs/CommandSpec/type",keyword:"type",params:{type: "object"},message:"must be object"}];
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
validate42.errors = [{instancePath,schemaPath:"#/type",keyword:"type",params:{type: "array"},message:"must be array"}];
return false;
}
}
validate42.errors = vErrors;
return errors === 0;
}
validate42.evaluated = {"items":true,"dynamicProps":false,"dynamicItems":false};

export const catalogue_error = validate43;
const schema70 = {"$schema":"https://json-schema.org/draft/2020-12/schema","additionalProperties":false,"properties":{"code":{"type":"string"},"message":{"type":"string"}},"required":["code","message"],"title":"ChatError","type":"object"};

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
if(errors === 0){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing0;
if(((data.code === undefined) && (missing0 = "code")) || ((data.message === undefined) && (missing0 = "message"))){
validate43.errors = [{instancePath,schemaPath:"#/required",keyword:"required",params:{missingProperty: missing0},message:"must have required property '"+missing0+"'"}];
return false;
}
else {
const _errs1 = errors;
for(const key0 in data){
if(!((key0 === "code") || (key0 === "message"))){
validate43.errors = [{instancePath,schemaPath:"#/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key0},message:"must NOT have additional properties"}];
return false;
break;
}
}
if(_errs1 === errors){
if(data.code !== undefined){
const _errs2 = errors;
if(typeof data.code !== "string"){
validate43.errors = [{instancePath:instancePath+"/code",schemaPath:"#/properties/code/type",keyword:"type",params:{type: "string"},message:"must be string"}];
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
validate43.errors = [{instancePath:instancePath+"/message",schemaPath:"#/properties/message/type",keyword:"type",params:{type: "string"},message:"must be string"}];
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
validate43.errors = [{instancePath,schemaPath:"#/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
validate43.errors = vErrors;
return errors === 0;
}
validate43.evaluated = {"props":true,"dynamicProps":false,"dynamicItems":false};

export const history_args = validate44;
const schema71 = {"$schema":"https://json-schema.org/draft/2020-12/schema","additionalProperties":false,"properties":{"before":{"type":["string","null"]},"conversation":{"type":"string"},"limit":{"format":"uint16","maximum":65535,"minimum":0,"type":"integer"}},"required":["conversation","limit"],"title":"ChatHistoryArgs","type":"object"};

function validate44(data, {instancePath="", parentData, parentDataProperty, rootData=data, dynamicAnchors={}}={}){
let vErrors = null;
let errors = 0;
const evaluated0 = validate44.evaluated;
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
validate44.errors = [{instancePath,schemaPath:"#/required",keyword:"required",params:{missingProperty: missing0},message:"must have required property '"+missing0+"'"}];
return false;
}
else {
const _errs1 = errors;
for(const key0 in data){
if(!(((key0 === "before") || (key0 === "conversation")) || (key0 === "limit"))){
validate44.errors = [{instancePath,schemaPath:"#/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key0},message:"must NOT have additional properties"}];
return false;
break;
}
}
if(_errs1 === errors){
if(data.before !== undefined){
let data0 = data.before;
const _errs2 = errors;
if((typeof data0 !== "string") && (data0 !== null)){
validate44.errors = [{instancePath:instancePath+"/before",schemaPath:"#/properties/before/type",keyword:"type",params:{type: schema71.properties.before.type},message:"must be string,null"}];
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
validate44.errors = [{instancePath:instancePath+"/conversation",schemaPath:"#/properties/conversation/type",keyword:"type",params:{type: "string"},message:"must be string"}];
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
validate44.errors = [{instancePath:instancePath+"/limit",schemaPath:"#/properties/limit/type",keyword:"type",params:{type: "integer"},message:"must be integer"}];
return false;
}
if(errors === _errs6){
if((typeof data2 == "number") && (isFinite(data2))){
if(data2 > 65535 || isNaN(data2)){
validate44.errors = [{instancePath:instancePath+"/limit",schemaPath:"#/properties/limit/maximum",keyword:"maximum",params:{comparison: "<=", limit: 65535},message:"must be <= 65535"}];
return false;
}
else {
if(data2 < 0 || isNaN(data2)){
validate44.errors = [{instancePath:instancePath+"/limit",schemaPath:"#/properties/limit/minimum",keyword:"minimum",params:{comparison: ">=", limit: 0},message:"must be >= 0"}];
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
validate44.errors = [{instancePath,schemaPath:"#/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
validate44.errors = vErrors;
return errors === 0;
}
validate44.evaluated = {"props":true,"dynamicProps":false,"dynamicItems":false};

export const history_output = validate45;
const schema72 = {"$defs":{"ActionResult":{"properties":{"artifacts":{"items":{"$ref":"#/$defs/Artifact"},"type":"array"},"details":{"items":{"type":"string"},"type":"array"},"id":{"type":"string"},"messageId":{"default":null,"type":["string","null"]},"outputBase64":{"description":"Exact signed bytes, base64 encoded; views decode only for display.","type":["string","null"]},"state":{"type":"string"},"stderr":{"type":"boolean"}},"required":["id","state","stderr","details","artifacts"],"type":"object"},"Artifact":{"properties":{"name":{"type":"string"},"url":{"type":"string"}},"required":["name","url"],"type":"object"},"Delivery":{"enum":["local_accepted"],"type":"string"},"Message":{"properties":{"body":{"type":"string"},"conversationId":{"type":"string"},"delivery":{"anyOf":[{"$ref":"#/$defs/Delivery"},{"type":"null"}],"description":"Local archive acceptance is the only fact currently available for outgoing text."},"id":{"type":"string"},"memberId":{"type":["string","null"]},"mine":{"type":"boolean"},"nickname":{"type":"string"},"result":{"anyOf":[{"$ref":"#/$defs/ActionResult"},{"type":"null"}],"default":null},"timestamp":{"format":"uint64","minimum":0,"type":"integer"}},"required":["id","conversationId","nickname","body","timestamp","mine"],"type":"object"}},"$schema":"https://json-schema.org/draft/2020-12/schema","properties":{"before":{"type":["string","null"]},"messages":{"items":{"$ref":"#/$defs/Message"},"type":"array"}},"required":["messages"],"title":"HistoryPage","type":"object"};
const schema73 = {"properties":{"body":{"type":"string"},"conversationId":{"type":"string"},"delivery":{"anyOf":[{"$ref":"#/$defs/Delivery"},{"type":"null"}],"description":"Local archive acceptance is the only fact currently available for outgoing text."},"id":{"type":"string"},"memberId":{"type":["string","null"]},"mine":{"type":"boolean"},"nickname":{"type":"string"},"result":{"anyOf":[{"$ref":"#/$defs/ActionResult"},{"type":"null"}],"default":null},"timestamp":{"format":"uint64","minimum":0,"type":"integer"}},"required":["id","conversationId","nickname","body","timestamp","mine"],"type":"object"};
const schema74 = {"enum":["local_accepted"],"type":"string"};
const schema75 = {"properties":{"artifacts":{"items":{"$ref":"#/$defs/Artifact"},"type":"array"},"details":{"items":{"type":"string"},"type":"array"},"id":{"type":"string"},"messageId":{"default":null,"type":["string","null"]},"outputBase64":{"description":"Exact signed bytes, base64 encoded; views decode only for display.","type":["string","null"]},"state":{"type":"string"},"stderr":{"type":"boolean"}},"required":["id","state","stderr","details","artifacts"],"type":"object"};
const schema76 = {"properties":{"name":{"type":"string"},"url":{"type":"string"}},"required":["name","url"],"type":"object"};

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
if((((((data.id === undefined) && (missing0 = "id")) || ((data.state === undefined) && (missing0 = "state"))) || ((data.stderr === undefined) && (missing0 = "stderr"))) || ((data.details === undefined) && (missing0 = "details"))) || ((data.artifacts === undefined) && (missing0 = "artifacts"))){
validate47.errors = [{instancePath,schemaPath:"#/required",keyword:"required",params:{missingProperty: missing0},message:"must have required property '"+missing0+"'"}];
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
validate47.errors = [{instancePath:instancePath+"/artifacts/" + i0,schemaPath:"#/$defs/Artifact/required",keyword:"required",params:{missingProperty: missing1},message:"must have required property '"+missing1+"'"}];
return false;
}
else {
if(data1.name !== undefined){
const _errs6 = errors;
if(typeof data1.name !== "string"){
validate47.errors = [{instancePath:instancePath+"/artifacts/" + i0+"/name",schemaPath:"#/$defs/Artifact/properties/name/type",keyword:"type",params:{type: "string"},message:"must be string"}];
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
validate47.errors = [{instancePath:instancePath+"/artifacts/" + i0+"/url",schemaPath:"#/$defs/Artifact/properties/url/type",keyword:"type",params:{type: "string"},message:"must be string"}];
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
validate47.errors = [{instancePath:instancePath+"/artifacts/" + i0,schemaPath:"#/$defs/Artifact/type",keyword:"type",params:{type: "object"},message:"must be object"}];
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
validate47.errors = [{instancePath:instancePath+"/artifacts",schemaPath:"#/properties/artifacts/type",keyword:"type",params:{type: "array"},message:"must be array"}];
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
validate47.errors = [{instancePath:instancePath+"/details/" + i1,schemaPath:"#/properties/details/items/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid4 = _errs12 === errors;
if(!valid4){
break;
}
}
}
else {
validate47.errors = [{instancePath:instancePath+"/details",schemaPath:"#/properties/details/type",keyword:"type",params:{type: "array"},message:"must be array"}];
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
validate47.errors = [{instancePath:instancePath+"/id",schemaPath:"#/properties/id/type",keyword:"type",params:{type: "string"},message:"must be string"}];
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
validate47.errors = [{instancePath:instancePath+"/messageId",schemaPath:"#/properties/messageId/type",keyword:"type",params:{type: schema75.properties.messageId.type},message:"must be string,null"}];
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
validate47.errors = [{instancePath:instancePath+"/outputBase64",schemaPath:"#/properties/outputBase64/type",keyword:"type",params:{type: schema75.properties.outputBase64.type},message:"must be string,null"}];
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
validate47.errors = [{instancePath:instancePath+"/state",schemaPath:"#/properties/state/type",keyword:"type",params:{type: "string"},message:"must be string"}];
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
validate47.errors = [{instancePath:instancePath+"/stderr",schemaPath:"#/properties/stderr/type",keyword:"type",params:{type: "boolean"},message:"must be boolean"}];
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
validate47.errors = [{instancePath,schemaPath:"#/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
validate47.errors = vErrors;
return errors === 0;
}
validate47.evaluated = {"props":{"artifacts":true,"details":true,"id":true,"messageId":true,"outputBase64":true,"state":true,"stderr":true},"dynamicProps":false,"dynamicItems":false};


function validate46(data, {instancePath="", parentData, parentDataProperty, rootData=data, dynamicAnchors={}}={}){
let vErrors = null;
let errors = 0;
const evaluated0 = validate46.evaluated;
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
validate46.errors = [{instancePath,schemaPath:"#/required",keyword:"required",params:{missingProperty: missing0},message:"must have required property '"+missing0+"'"}];
return false;
}
else {
if(data.body !== undefined){
const _errs1 = errors;
if(typeof data.body !== "string"){
validate46.errors = [{instancePath:instancePath+"/body",schemaPath:"#/properties/body/type",keyword:"type",params:{type: "string"},message:"must be string"}];
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
validate46.errors = [{instancePath:instancePath+"/conversationId",schemaPath:"#/properties/conversationId/type",keyword:"type",params:{type: "string"},message:"must be string"}];
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
if(!(data2 === "local_accepted")){
const err1 = {instancePath:instancePath+"/delivery",schemaPath:"#/$defs/Delivery/enum",keyword:"enum",params:{allowedValues: schema74.enum},message:"must be equal to one of the allowed values"};
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
validate46.errors = vErrors;
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
validate46.errors = [{instancePath:instancePath+"/id",schemaPath:"#/properties/id/type",keyword:"type",params:{type: "string"},message:"must be string"}];
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
validate46.errors = [{instancePath:instancePath+"/memberId",schemaPath:"#/properties/memberId/type",keyword:"type",params:{type: schema73.properties.memberId.type},message:"must be string,null"}];
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
validate46.errors = [{instancePath:instancePath+"/mine",schemaPath:"#/properties/mine/type",keyword:"type",params:{type: "boolean"},message:"must be boolean"}];
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
validate46.errors = [{instancePath:instancePath+"/nickname",schemaPath:"#/properties/nickname/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs18 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.result !== undefined){
let data7 = data.result;
const _errs20 = errors;
const _errs21 = errors;
let valid3 = false;
const _errs22 = errors;
if(!(validate47(data7, {instancePath:instancePath+"/result",parentData:data,parentDataProperty:"result",rootData,dynamicAnchors}))){
vErrors = vErrors === null ? validate47.errors : vErrors.concat(validate47.errors);
errors = vErrors.length;
}
var _valid1 = _errs22 === errors;
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
const _errs23 = errors;
if(data7 !== null){
const err4 = {instancePath:instancePath+"/result",schemaPath:"#/properties/result/anyOf/1/type",keyword:"type",params:{type: "null"},message:"must be null"};
if(vErrors === null){
vErrors = [err4];
}
else {
vErrors.push(err4);
}
errors++;
}
var _valid1 = _errs23 === errors;
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
validate46.errors = vErrors;
return false;
}
else {
errors = _errs21;
if(vErrors !== null){
if(_errs21){
vErrors.length = _errs21;
}
else {
vErrors = null;
}
}
}
var valid0 = _errs20 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.timestamp !== undefined){
let data8 = data.timestamp;
const _errs25 = errors;
if(!(((typeof data8 == "number") && (!(data8 % 1) && !isNaN(data8))) && (isFinite(data8)))){
validate46.errors = [{instancePath:instancePath+"/timestamp",schemaPath:"#/properties/timestamp/type",keyword:"type",params:{type: "integer"},message:"must be integer"}];
return false;
}
if(errors === _errs25){
if((typeof data8 == "number") && (isFinite(data8))){
if(data8 < 0 || isNaN(data8)){
validate46.errors = [{instancePath:instancePath+"/timestamp",schemaPath:"#/properties/timestamp/minimum",keyword:"minimum",params:{comparison: ">=", limit: 0},message:"must be >= 0"}];
return false;
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
else {
validate46.errors = [{instancePath,schemaPath:"#/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
validate46.errors = vErrors;
return errors === 0;
}
validate46.evaluated = {"props":{"body":true,"conversationId":true,"delivery":true,"id":true,"memberId":true,"mine":true,"nickname":true,"result":true,"timestamp":true},"dynamicProps":false,"dynamicItems":false};


function validate45(data, {instancePath="", parentData, parentDataProperty, rootData=data, dynamicAnchors={}}={}){
let vErrors = null;
let errors = 0;
const evaluated0 = validate45.evaluated;
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
validate45.errors = [{instancePath,schemaPath:"#/required",keyword:"required",params:{missingProperty: missing0},message:"must have required property '"+missing0+"'"}];
return false;
}
else {
if(data.before !== undefined){
let data0 = data.before;
const _errs1 = errors;
if((typeof data0 !== "string") && (data0 !== null)){
validate45.errors = [{instancePath:instancePath+"/before",schemaPath:"#/properties/before/type",keyword:"type",params:{type: schema72.properties.before.type},message:"must be string,null"}];
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
if(!(validate46(data1[i0], {instancePath:instancePath+"/messages/" + i0,parentData:data1,parentDataProperty:i0,rootData,dynamicAnchors}))){
vErrors = vErrors === null ? validate46.errors : vErrors.concat(validate46.errors);
errors = vErrors.length;
}
var valid1 = _errs5 === errors;
if(!valid1){
break;
}
}
}
else {
validate45.errors = [{instancePath:instancePath+"/messages",schemaPath:"#/properties/messages/type",keyword:"type",params:{type: "array"},message:"must be array"}];
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
validate45.errors = [{instancePath,schemaPath:"#/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
validate45.errors = vErrors;
return errors === 0;
}
validate45.evaluated = {"props":{"before":true,"messages":true},"dynamicProps":false,"dynamicItems":false};

export const history_error = validate50;
const schema77 = {"$schema":"https://json-schema.org/draft/2020-12/schema","additionalProperties":false,"properties":{"code":{"type":"string"},"message":{"type":"string"}},"required":["code","message"],"title":"ChatError","type":"object"};

function validate50(data, {instancePath="", parentData, parentDataProperty, rootData=data, dynamicAnchors={}}={}){
let vErrors = null;
let errors = 0;
const evaluated0 = validate50.evaluated;
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
validate50.errors = [{instancePath,schemaPath:"#/required",keyword:"required",params:{missingProperty: missing0},message:"must have required property '"+missing0+"'"}];
return false;
}
else {
const _errs1 = errors;
for(const key0 in data){
if(!((key0 === "code") || (key0 === "message"))){
validate50.errors = [{instancePath,schemaPath:"#/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key0},message:"must NOT have additional properties"}];
return false;
break;
}
}
if(_errs1 === errors){
if(data.code !== undefined){
const _errs2 = errors;
if(typeof data.code !== "string"){
validate50.errors = [{instancePath:instancePath+"/code",schemaPath:"#/properties/code/type",keyword:"type",params:{type: "string"},message:"must be string"}];
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
validate50.errors = [{instancePath:instancePath+"/message",schemaPath:"#/properties/message/type",keyword:"type",params:{type: "string"},message:"must be string"}];
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
validate50.errors = [{instancePath,schemaPath:"#/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
validate50.errors = vErrors;
return errors === 0;
}
validate50.evaluated = {"props":true,"dynamicProps":false,"dynamicItems":false};

export const search_args = validate51;
const schema78 = {"$schema":"https://json-schema.org/draft/2020-12/schema","additionalProperties":false,"properties":{"before":{"type":["string","null"]},"conversation":{"type":"string"},"limit":{"format":"uint16","maximum":65535,"minimum":0,"type":"integer"},"text":{"type":"string"}},"required":["conversation","text","limit"],"title":"ChatSearchArgs","type":"object"};

function validate51(data, {instancePath="", parentData, parentDataProperty, rootData=data, dynamicAnchors={}}={}){
let vErrors = null;
let errors = 0;
const evaluated0 = validate51.evaluated;
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
validate51.errors = [{instancePath,schemaPath:"#/required",keyword:"required",params:{missingProperty: missing0},message:"must have required property '"+missing0+"'"}];
return false;
}
else {
const _errs1 = errors;
for(const key0 in data){
if(!((((key0 === "before") || (key0 === "conversation")) || (key0 === "limit")) || (key0 === "text"))){
validate51.errors = [{instancePath,schemaPath:"#/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key0},message:"must NOT have additional properties"}];
return false;
break;
}
}
if(_errs1 === errors){
if(data.before !== undefined){
let data0 = data.before;
const _errs2 = errors;
if((typeof data0 !== "string") && (data0 !== null)){
validate51.errors = [{instancePath:instancePath+"/before",schemaPath:"#/properties/before/type",keyword:"type",params:{type: schema78.properties.before.type},message:"must be string,null"}];
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
validate51.errors = [{instancePath:instancePath+"/conversation",schemaPath:"#/properties/conversation/type",keyword:"type",params:{type: "string"},message:"must be string"}];
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
validate51.errors = [{instancePath:instancePath+"/limit",schemaPath:"#/properties/limit/type",keyword:"type",params:{type: "integer"},message:"must be integer"}];
return false;
}
if(errors === _errs6){
if((typeof data2 == "number") && (isFinite(data2))){
if(data2 > 65535 || isNaN(data2)){
validate51.errors = [{instancePath:instancePath+"/limit",schemaPath:"#/properties/limit/maximum",keyword:"maximum",params:{comparison: "<=", limit: 65535},message:"must be <= 65535"}];
return false;
}
else {
if(data2 < 0 || isNaN(data2)){
validate51.errors = [{instancePath:instancePath+"/limit",schemaPath:"#/properties/limit/minimum",keyword:"minimum",params:{comparison: ">=", limit: 0},message:"must be >= 0"}];
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
validate51.errors = [{instancePath:instancePath+"/text",schemaPath:"#/properties/text/type",keyword:"type",params:{type: "string"},message:"must be string"}];
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
validate51.errors = [{instancePath,schemaPath:"#/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
validate51.errors = vErrors;
return errors === 0;
}
validate51.evaluated = {"props":true,"dynamicProps":false,"dynamicItems":false};

export const search_output = validate52;
const schema79 = {"$defs":{"ActionResult":{"properties":{"artifacts":{"items":{"$ref":"#/$defs/Artifact"},"type":"array"},"details":{"items":{"type":"string"},"type":"array"},"id":{"type":"string"},"messageId":{"default":null,"type":["string","null"]},"outputBase64":{"description":"Exact signed bytes, base64 encoded; views decode only for display.","type":["string","null"]},"state":{"type":"string"},"stderr":{"type":"boolean"}},"required":["id","state","stderr","details","artifacts"],"type":"object"},"Artifact":{"properties":{"name":{"type":"string"},"url":{"type":"string"}},"required":["name","url"],"type":"object"},"Delivery":{"enum":["local_accepted"],"type":"string"},"Message":{"properties":{"body":{"type":"string"},"conversationId":{"type":"string"},"delivery":{"anyOf":[{"$ref":"#/$defs/Delivery"},{"type":"null"}],"description":"Local archive acceptance is the only fact currently available for outgoing text."},"id":{"type":"string"},"memberId":{"type":["string","null"]},"mine":{"type":"boolean"},"nickname":{"type":"string"},"result":{"anyOf":[{"$ref":"#/$defs/ActionResult"},{"type":"null"}],"default":null},"timestamp":{"format":"uint64","minimum":0,"type":"integer"}},"required":["id","conversationId","nickname","body","timestamp","mine"],"type":"object"}},"$schema":"https://json-schema.org/draft/2020-12/schema","properties":{"before":{"type":["string","null"]},"messages":{"items":{"$ref":"#/$defs/Message"},"type":"array"}},"required":["messages"],"title":"HistoryPage","type":"object"};
const schema80 = {"properties":{"body":{"type":"string"},"conversationId":{"type":"string"},"delivery":{"anyOf":[{"$ref":"#/$defs/Delivery"},{"type":"null"}],"description":"Local archive acceptance is the only fact currently available for outgoing text."},"id":{"type":"string"},"memberId":{"type":["string","null"]},"mine":{"type":"boolean"},"nickname":{"type":"string"},"result":{"anyOf":[{"$ref":"#/$defs/ActionResult"},{"type":"null"}],"default":null},"timestamp":{"format":"uint64","minimum":0,"type":"integer"}},"required":["id","conversationId","nickname","body","timestamp","mine"],"type":"object"};
const schema81 = {"enum":["local_accepted"],"type":"string"};
const schema82 = {"properties":{"artifacts":{"items":{"$ref":"#/$defs/Artifact"},"type":"array"},"details":{"items":{"type":"string"},"type":"array"},"id":{"type":"string"},"messageId":{"default":null,"type":["string","null"]},"outputBase64":{"description":"Exact signed bytes, base64 encoded; views decode only for display.","type":["string","null"]},"state":{"type":"string"},"stderr":{"type":"boolean"}},"required":["id","state","stderr","details","artifacts"],"type":"object"};
const schema83 = {"properties":{"name":{"type":"string"},"url":{"type":"string"}},"required":["name","url"],"type":"object"};

function validate54(data, {instancePath="", parentData, parentDataProperty, rootData=data, dynamicAnchors={}}={}){
let vErrors = null;
let errors = 0;
const evaluated0 = validate54.evaluated;
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
validate54.errors = [{instancePath,schemaPath:"#/required",keyword:"required",params:{missingProperty: missing0},message:"must have required property '"+missing0+"'"}];
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
validate54.errors = [{instancePath:instancePath+"/artifacts/" + i0,schemaPath:"#/$defs/Artifact/required",keyword:"required",params:{missingProperty: missing1},message:"must have required property '"+missing1+"'"}];
return false;
}
else {
if(data1.name !== undefined){
const _errs6 = errors;
if(typeof data1.name !== "string"){
validate54.errors = [{instancePath:instancePath+"/artifacts/" + i0+"/name",schemaPath:"#/$defs/Artifact/properties/name/type",keyword:"type",params:{type: "string"},message:"must be string"}];
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
validate54.errors = [{instancePath:instancePath+"/artifacts/" + i0+"/url",schemaPath:"#/$defs/Artifact/properties/url/type",keyword:"type",params:{type: "string"},message:"must be string"}];
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
validate54.errors = [{instancePath:instancePath+"/artifacts/" + i0,schemaPath:"#/$defs/Artifact/type",keyword:"type",params:{type: "object"},message:"must be object"}];
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
validate54.errors = [{instancePath:instancePath+"/artifacts",schemaPath:"#/properties/artifacts/type",keyword:"type",params:{type: "array"},message:"must be array"}];
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
validate54.errors = [{instancePath:instancePath+"/details/" + i1,schemaPath:"#/properties/details/items/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid4 = _errs12 === errors;
if(!valid4){
break;
}
}
}
else {
validate54.errors = [{instancePath:instancePath+"/details",schemaPath:"#/properties/details/type",keyword:"type",params:{type: "array"},message:"must be array"}];
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
validate54.errors = [{instancePath:instancePath+"/id",schemaPath:"#/properties/id/type",keyword:"type",params:{type: "string"},message:"must be string"}];
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
validate54.errors = [{instancePath:instancePath+"/messageId",schemaPath:"#/properties/messageId/type",keyword:"type",params:{type: schema82.properties.messageId.type},message:"must be string,null"}];
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
validate54.errors = [{instancePath:instancePath+"/outputBase64",schemaPath:"#/properties/outputBase64/type",keyword:"type",params:{type: schema82.properties.outputBase64.type},message:"must be string,null"}];
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
validate54.errors = [{instancePath:instancePath+"/state",schemaPath:"#/properties/state/type",keyword:"type",params:{type: "string"},message:"must be string"}];
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
validate54.errors = [{instancePath:instancePath+"/stderr",schemaPath:"#/properties/stderr/type",keyword:"type",params:{type: "boolean"},message:"must be boolean"}];
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
validate54.errors = [{instancePath,schemaPath:"#/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
validate54.errors = vErrors;
return errors === 0;
}
validate54.evaluated = {"props":{"artifacts":true,"details":true,"id":true,"messageId":true,"outputBase64":true,"state":true,"stderr":true},"dynamicProps":false,"dynamicItems":false};


function validate53(data, {instancePath="", parentData, parentDataProperty, rootData=data, dynamicAnchors={}}={}){
let vErrors = null;
let errors = 0;
const evaluated0 = validate53.evaluated;
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
validate53.errors = [{instancePath,schemaPath:"#/required",keyword:"required",params:{missingProperty: missing0},message:"must have required property '"+missing0+"'"}];
return false;
}
else {
if(data.body !== undefined){
const _errs1 = errors;
if(typeof data.body !== "string"){
validate53.errors = [{instancePath:instancePath+"/body",schemaPath:"#/properties/body/type",keyword:"type",params:{type: "string"},message:"must be string"}];
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
validate53.errors = [{instancePath:instancePath+"/conversationId",schemaPath:"#/properties/conversationId/type",keyword:"type",params:{type: "string"},message:"must be string"}];
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
if(!(data2 === "local_accepted")){
const err1 = {instancePath:instancePath+"/delivery",schemaPath:"#/$defs/Delivery/enum",keyword:"enum",params:{allowedValues: schema81.enum},message:"must be equal to one of the allowed values"};
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
validate53.errors = vErrors;
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
validate53.errors = [{instancePath:instancePath+"/id",schemaPath:"#/properties/id/type",keyword:"type",params:{type: "string"},message:"must be string"}];
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
validate53.errors = [{instancePath:instancePath+"/memberId",schemaPath:"#/properties/memberId/type",keyword:"type",params:{type: schema80.properties.memberId.type},message:"must be string,null"}];
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
validate53.errors = [{instancePath:instancePath+"/mine",schemaPath:"#/properties/mine/type",keyword:"type",params:{type: "boolean"},message:"must be boolean"}];
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
validate53.errors = [{instancePath:instancePath+"/nickname",schemaPath:"#/properties/nickname/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid0 = _errs18 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.result !== undefined){
let data7 = data.result;
const _errs20 = errors;
const _errs21 = errors;
let valid3 = false;
const _errs22 = errors;
if(!(validate54(data7, {instancePath:instancePath+"/result",parentData:data,parentDataProperty:"result",rootData,dynamicAnchors}))){
vErrors = vErrors === null ? validate54.errors : vErrors.concat(validate54.errors);
errors = vErrors.length;
}
var _valid1 = _errs22 === errors;
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
const _errs23 = errors;
if(data7 !== null){
const err4 = {instancePath:instancePath+"/result",schemaPath:"#/properties/result/anyOf/1/type",keyword:"type",params:{type: "null"},message:"must be null"};
if(vErrors === null){
vErrors = [err4];
}
else {
vErrors.push(err4);
}
errors++;
}
var _valid1 = _errs23 === errors;
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
validate53.errors = vErrors;
return false;
}
else {
errors = _errs21;
if(vErrors !== null){
if(_errs21){
vErrors.length = _errs21;
}
else {
vErrors = null;
}
}
}
var valid0 = _errs20 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.timestamp !== undefined){
let data8 = data.timestamp;
const _errs25 = errors;
if(!(((typeof data8 == "number") && (!(data8 % 1) && !isNaN(data8))) && (isFinite(data8)))){
validate53.errors = [{instancePath:instancePath+"/timestamp",schemaPath:"#/properties/timestamp/type",keyword:"type",params:{type: "integer"},message:"must be integer"}];
return false;
}
if(errors === _errs25){
if((typeof data8 == "number") && (isFinite(data8))){
if(data8 < 0 || isNaN(data8)){
validate53.errors = [{instancePath:instancePath+"/timestamp",schemaPath:"#/properties/timestamp/minimum",keyword:"minimum",params:{comparison: ">=", limit: 0},message:"must be >= 0"}];
return false;
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
else {
validate53.errors = [{instancePath,schemaPath:"#/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
validate53.errors = vErrors;
return errors === 0;
}
validate53.evaluated = {"props":{"body":true,"conversationId":true,"delivery":true,"id":true,"memberId":true,"mine":true,"nickname":true,"result":true,"timestamp":true},"dynamicProps":false,"dynamicItems":false};


function validate52(data, {instancePath="", parentData, parentDataProperty, rootData=data, dynamicAnchors={}}={}){
let vErrors = null;
let errors = 0;
const evaluated0 = validate52.evaluated;
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
validate52.errors = [{instancePath,schemaPath:"#/required",keyword:"required",params:{missingProperty: missing0},message:"must have required property '"+missing0+"'"}];
return false;
}
else {
if(data.before !== undefined){
let data0 = data.before;
const _errs1 = errors;
if((typeof data0 !== "string") && (data0 !== null)){
validate52.errors = [{instancePath:instancePath+"/before",schemaPath:"#/properties/before/type",keyword:"type",params:{type: schema79.properties.before.type},message:"must be string,null"}];
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
if(!(validate53(data1[i0], {instancePath:instancePath+"/messages/" + i0,parentData:data1,parentDataProperty:i0,rootData,dynamicAnchors}))){
vErrors = vErrors === null ? validate53.errors : vErrors.concat(validate53.errors);
errors = vErrors.length;
}
var valid1 = _errs5 === errors;
if(!valid1){
break;
}
}
}
else {
validate52.errors = [{instancePath:instancePath+"/messages",schemaPath:"#/properties/messages/type",keyword:"type",params:{type: "array"},message:"must be array"}];
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
validate52.errors = [{instancePath,schemaPath:"#/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
validate52.errors = vErrors;
return errors === 0;
}
validate52.evaluated = {"props":{"before":true,"messages":true},"dynamicProps":false,"dynamicItems":false};

export const search_error = validate57;
const schema84 = {"$schema":"https://json-schema.org/draft/2020-12/schema","additionalProperties":false,"properties":{"code":{"type":"string"},"message":{"type":"string"}},"required":["code","message"],"title":"ChatError","type":"object"};

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
if(((data.code === undefined) && (missing0 = "code")) || ((data.message === undefined) && (missing0 = "message"))){
validate57.errors = [{instancePath,schemaPath:"#/required",keyword:"required",params:{missingProperty: missing0},message:"must have required property '"+missing0+"'"}];
return false;
}
else {
const _errs1 = errors;
for(const key0 in data){
if(!((key0 === "code") || (key0 === "message"))){
validate57.errors = [{instancePath,schemaPath:"#/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key0},message:"must NOT have additional properties"}];
return false;
break;
}
}
if(_errs1 === errors){
if(data.code !== undefined){
const _errs2 = errors;
if(typeof data.code !== "string"){
validate57.errors = [{instancePath:instancePath+"/code",schemaPath:"#/properties/code/type",keyword:"type",params:{type: "string"},message:"must be string"}];
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
validate57.errors = [{instancePath:instancePath+"/message",schemaPath:"#/properties/message/type",keyword:"type",params:{type: "string"},message:"must be string"}];
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
validate57.errors = [{instancePath,schemaPath:"#/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
validate57.errors = vErrors;
return errors === 0;
}
validate57.evaluated = {"props":true,"dynamicProps":false,"dynamicItems":false};

export const submit_args = validate58;
const schema85 = {"$schema":"https://json-schema.org/draft/2020-12/schema","additionalProperties":false,"properties":{"conversation":{"type":["string","null"]},"text":{"type":"string"}},"required":["text"],"title":"ChatSubmitArgs","type":"object"};

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
if(errors === 0){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing0;
if((data.text === undefined) && (missing0 = "text")){
validate58.errors = [{instancePath,schemaPath:"#/required",keyword:"required",params:{missingProperty: missing0},message:"must have required property '"+missing0+"'"}];
return false;
}
else {
const _errs1 = errors;
for(const key0 in data){
if(!((key0 === "conversation") || (key0 === "text"))){
validate58.errors = [{instancePath,schemaPath:"#/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key0},message:"must NOT have additional properties"}];
return false;
break;
}
}
if(_errs1 === errors){
if(data.conversation !== undefined){
let data0 = data.conversation;
const _errs2 = errors;
if((typeof data0 !== "string") && (data0 !== null)){
validate58.errors = [{instancePath:instancePath+"/conversation",schemaPath:"#/properties/conversation/type",keyword:"type",params:{type: schema85.properties.conversation.type},message:"must be string,null"}];
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
validate58.errors = [{instancePath:instancePath+"/text",schemaPath:"#/properties/text/type",keyword:"type",params:{type: "string"},message:"must be string"}];
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
validate58.errors = [{instancePath,schemaPath:"#/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
validate58.errors = vErrors;
return errors === 0;
}
validate58.evaluated = {"props":true,"dynamicProps":false,"dynamicItems":false};

export const submit_output = validate59;
const schema86 = {"$defs":{"CommandOutput":{"oneOf":[{"properties":{"commands":{"items":{"$ref":"#/$defs/CommandSpec"},"type":"array"},"kind":{"const":"help","type":"string"}},"required":["kind","commands"],"type":"object"},{"properties":{"channels":{"items":{"$ref":"#/$defs/DirectoryEntry"},"type":"array"},"kind":{"const":"directory","type":"string"}},"required":["kind","channels"],"type":"object"},{"properties":{"channel":{"type":"string"},"expires":{"format":"uint64","minimum":0,"type":"integer"},"kind":{"const":"invitation","type":"string"},"link":{"type":"string"},"localOnly":{"default":false,"type":"boolean"}},"required":["kind","channel","link","expires"],"type":"object"},{"properties":{"kind":{"const":"text","type":"string"},"text":{"type":"string"},"title":{"type":"string"}},"required":["kind","title","text"],"type":"object"},{"properties":{"kind":{"const":"status","type":"string"},"text":{"type":"string"}},"required":["kind","text"],"type":"object"},{"properties":{"conversation":{"type":"string"},"kind":{"const":"close","type":"string"}},"required":["kind","conversation"],"type":"object"}]},"CommandSpec":{"properties":{"available":{"type":"boolean"},"capability":{"type":["string","null"]},"description":{"type":"string"},"name":{"type":"string"},"scope":{"type":"string"},"usage":{"type":"string"}},"required":["name","usage","description","scope","available"],"type":"object"},"DirectoryEntry":{"properties":{"conversation":{"type":["string","null"]},"joined":{"type":"boolean"},"name":{"type":"string"}},"required":["name","joined"],"type":"object"}},"$schema":"https://json-schema.org/draft/2020-12/schema","oneOf":[{"additionalProperties":false,"properties":{"conversation":{"type":["string","null"]},"kind":{"const":"applied","type":"string"},"notice":{"type":["string","null"]}},"required":["kind"],"type":"object"},{"additionalProperties":false,"properties":{"conversation":{"type":["string","null"]},"kind":{"const":"output","type":"string"},"output":{"$ref":"#/$defs/CommandOutput"}},"required":["kind","output"],"type":"object"}],"title":"SubmitOutcome"};
const schema87 = {"oneOf":[{"properties":{"commands":{"items":{"$ref":"#/$defs/CommandSpec"},"type":"array"},"kind":{"const":"help","type":"string"}},"required":["kind","commands"],"type":"object"},{"properties":{"channels":{"items":{"$ref":"#/$defs/DirectoryEntry"},"type":"array"},"kind":{"const":"directory","type":"string"}},"required":["kind","channels"],"type":"object"},{"properties":{"channel":{"type":"string"},"expires":{"format":"uint64","minimum":0,"type":"integer"},"kind":{"const":"invitation","type":"string"},"link":{"type":"string"},"localOnly":{"default":false,"type":"boolean"}},"required":["kind","channel","link","expires"],"type":"object"},{"properties":{"kind":{"const":"text","type":"string"},"text":{"type":"string"},"title":{"type":"string"}},"required":["kind","title","text"],"type":"object"},{"properties":{"kind":{"const":"status","type":"string"},"text":{"type":"string"}},"required":["kind","text"],"type":"object"},{"properties":{"conversation":{"type":"string"},"kind":{"const":"close","type":"string"}},"required":["kind","conversation"],"type":"object"}]};
const schema88 = {"properties":{"available":{"type":"boolean"},"capability":{"type":["string","null"]},"description":{"type":"string"},"name":{"type":"string"},"scope":{"type":"string"},"usage":{"type":"string"}},"required":["name","usage","description","scope","available"],"type":"object"};
const schema89 = {"properties":{"conversation":{"type":["string","null"]},"joined":{"type":"boolean"},"name":{"type":"string"}},"required":["name","joined"],"type":"object"};

function validate60(data, {instancePath="", parentData, parentDataProperty, rootData=data, dynamicAnchors={}}={}){
let vErrors = null;
let errors = 0;
const evaluated0 = validate60.evaluated;
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
const err3 = {instancePath:instancePath+"/commands/" + i0+"/capability",schemaPath:"#/$defs/CommandSpec/properties/capability/type",keyword:"type",params:{type: schema88.properties.capability.type},message:"must be string,null"};
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
const err15 = {instancePath:instancePath+"/channels/" + i1+"/conversation",schemaPath:"#/$defs/DirectoryEntry/properties/conversation/type",keyword:"type",params:{type: schema89.properties.conversation.type},message:"must be string,null"};
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
validate60.errors = vErrors;
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
validate60.errors = vErrors;
evaluated0.props = props0;
return errors === 0;
}
validate60.evaluated = {"dynamicProps":true,"dynamicItems":false};


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
const err2 = {instancePath:instancePath+"/conversation",schemaPath:"#/oneOf/0/properties/conversation/type",keyword:"type",params:{type: schema86.oneOf[0].properties.conversation.type},message:"must be string,null"};
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
const err5 = {instancePath:instancePath+"/notice",schemaPath:"#/oneOf/0/properties/notice/type",keyword:"type",params:{type: schema86.oneOf[0].properties.notice.type},message:"must be string,null"};
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
const err9 = {instancePath:instancePath+"/conversation",schemaPath:"#/oneOf/1/properties/conversation/type",keyword:"type",params:{type: schema86.oneOf[1].properties.conversation.type},message:"must be string,null"};
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
if(!(validate60(data.output, {instancePath:instancePath+"/output",parentData:data,parentDataProperty:"output",rootData,dynamicAnchors}))){
vErrors = vErrors === null ? validate60.errors : vErrors.concat(validate60.errors);
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
evaluated0.props = props0;
return errors === 0;
}
validate59.evaluated = {"dynamicProps":true,"dynamicItems":false};

export const submit_error = validate62;
const schema90 = {"$schema":"https://json-schema.org/draft/2020-12/schema","additionalProperties":false,"properties":{"code":{"type":"string"},"message":{"type":"string"}},"required":["code","message"],"title":"ChatError","type":"object"};

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
if(errors === 0){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing0;
if(((data.code === undefined) && (missing0 = "code")) || ((data.message === undefined) && (missing0 = "message"))){
validate62.errors = [{instancePath,schemaPath:"#/required",keyword:"required",params:{missingProperty: missing0},message:"must have required property '"+missing0+"'"}];
return false;
}
else {
const _errs1 = errors;
for(const key0 in data){
if(!((key0 === "code") || (key0 === "message"))){
validate62.errors = [{instancePath,schemaPath:"#/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key0},message:"must NOT have additional properties"}];
return false;
break;
}
}
if(_errs1 === errors){
if(data.code !== undefined){
const _errs2 = errors;
if(typeof data.code !== "string"){
validate62.errors = [{instancePath:instancePath+"/code",schemaPath:"#/properties/code/type",keyword:"type",params:{type: "string"},message:"must be string"}];
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
validate62.errors = [{instancePath:instancePath+"/message",schemaPath:"#/properties/message/type",keyword:"type",params:{type: "string"},message:"must be string"}];
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
validate62.errors = [{instancePath,schemaPath:"#/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
validate62.errors = vErrors;
return errors === 0;
}
validate62.evaluated = {"props":true,"dynamicProps":false,"dynamicItems":false};

export const complete_args = validate63;
const schema91 = {"$schema":"https://json-schema.org/draft/2020-12/schema","additionalProperties":false,"properties":{"conversation":{"type":["string","null"]},"text":{"type":"string"}},"required":["text"],"title":"ChatCompleteArgs","type":"object"};

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
if((data.text === undefined) && (missing0 = "text")){
validate63.errors = [{instancePath,schemaPath:"#/required",keyword:"required",params:{missingProperty: missing0},message:"must have required property '"+missing0+"'"}];
return false;
}
else {
const _errs1 = errors;
for(const key0 in data){
if(!((key0 === "conversation") || (key0 === "text"))){
validate63.errors = [{instancePath,schemaPath:"#/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key0},message:"must NOT have additional properties"}];
return false;
break;
}
}
if(_errs1 === errors){
if(data.conversation !== undefined){
let data0 = data.conversation;
const _errs2 = errors;
if((typeof data0 !== "string") && (data0 !== null)){
validate63.errors = [{instancePath:instancePath+"/conversation",schemaPath:"#/properties/conversation/type",keyword:"type",params:{type: schema91.properties.conversation.type},message:"must be string,null"}];
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
validate63.errors = [{instancePath:instancePath+"/text",schemaPath:"#/properties/text/type",keyword:"type",params:{type: "string"},message:"must be string"}];
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
validate63.errors = [{instancePath,schemaPath:"#/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
validate63.errors = vErrors;
return errors === 0;
}
validate63.evaluated = {"props":true,"dynamicProps":false,"dynamicItems":false};

export const complete_output = validate64;
const schema92 = {"$defs":{"Completion":{"properties":{"description":{"type":"string"},"text":{"type":"string"}},"required":["text","description"],"type":"object"}},"$schema":"https://json-schema.org/draft/2020-12/schema","items":{"$ref":"#/$defs/Completion"},"title":"Array_of_Completion","type":"array"};
const schema93 = {"properties":{"description":{"type":"string"},"text":{"type":"string"}},"required":["text","description"],"type":"object"};

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
validate64.errors = [{instancePath:instancePath+"/" + i0,schemaPath:"#/$defs/Completion/required",keyword:"required",params:{missingProperty: missing0},message:"must have required property '"+missing0+"'"}];
return false;
}
else {
if(data0.description !== undefined){
const _errs4 = errors;
if(typeof data0.description !== "string"){
validate64.errors = [{instancePath:instancePath+"/" + i0+"/description",schemaPath:"#/$defs/Completion/properties/description/type",keyword:"type",params:{type: "string"},message:"must be string"}];
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
validate64.errors = [{instancePath:instancePath+"/" + i0+"/text",schemaPath:"#/$defs/Completion/properties/text/type",keyword:"type",params:{type: "string"},message:"must be string"}];
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
validate64.errors = [{instancePath:instancePath+"/" + i0,schemaPath:"#/$defs/Completion/type",keyword:"type",params:{type: "object"},message:"must be object"}];
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
validate64.errors = [{instancePath,schemaPath:"#/type",keyword:"type",params:{type: "array"},message:"must be array"}];
return false;
}
}
validate64.errors = vErrors;
return errors === 0;
}
validate64.evaluated = {"items":true,"dynamicProps":false,"dynamicItems":false};

export const complete_error = validate65;
const schema94 = {"$schema":"https://json-schema.org/draft/2020-12/schema","additionalProperties":false,"properties":{"code":{"type":"string"},"message":{"type":"string"}},"required":["code","message"],"title":"ChatError","type":"object"};

function validate65(data, {instancePath="", parentData, parentDataProperty, rootData=data, dynamicAnchors={}}={}){
let vErrors = null;
let errors = 0;
const evaluated0 = validate65.evaluated;
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
validate65.errors = [{instancePath,schemaPath:"#/required",keyword:"required",params:{missingProperty: missing0},message:"must have required property '"+missing0+"'"}];
return false;
}
else {
const _errs1 = errors;
for(const key0 in data){
if(!((key0 === "code") || (key0 === "message"))){
validate65.errors = [{instancePath,schemaPath:"#/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key0},message:"must NOT have additional properties"}];
return false;
break;
}
}
if(_errs1 === errors){
if(data.code !== undefined){
const _errs2 = errors;
if(typeof data.code !== "string"){
validate65.errors = [{instancePath:instancePath+"/code",schemaPath:"#/properties/code/type",keyword:"type",params:{type: "string"},message:"must be string"}];
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
validate65.errors = [{instancePath:instancePath+"/message",schemaPath:"#/properties/message/type",keyword:"type",params:{type: "string"},message:"must be string"}];
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
validate65.errors = [{instancePath,schemaPath:"#/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
validate65.errors = vErrors;
return errors === 0;
}
validate65.evaluated = {"props":true,"dynamicProps":false,"dynamicItems":false};

export const mark_read_args = validate66;
const schema95 = {"$schema":"https://json-schema.org/draft/2020-12/schema","additionalProperties":false,"properties":{"conversation":{"type":"string"},"message_id":{"type":"string"}},"required":["conversation","message_id"],"title":"ChatMarkReadArgs","type":"object"};

function validate66(data, {instancePath="", parentData, parentDataProperty, rootData=data, dynamicAnchors={}}={}){
let vErrors = null;
let errors = 0;
const evaluated0 = validate66.evaluated;
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
validate66.errors = [{instancePath,schemaPath:"#/required",keyword:"required",params:{missingProperty: missing0},message:"must have required property '"+missing0+"'"}];
return false;
}
else {
const _errs1 = errors;
for(const key0 in data){
if(!((key0 === "conversation") || (key0 === "message_id"))){
validate66.errors = [{instancePath,schemaPath:"#/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key0},message:"must NOT have additional properties"}];
return false;
break;
}
}
if(_errs1 === errors){
if(data.conversation !== undefined){
const _errs2 = errors;
if(typeof data.conversation !== "string"){
validate66.errors = [{instancePath:instancePath+"/conversation",schemaPath:"#/properties/conversation/type",keyword:"type",params:{type: "string"},message:"must be string"}];
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
validate66.errors = [{instancePath:instancePath+"/message_id",schemaPath:"#/properties/message_id/type",keyword:"type",params:{type: "string"},message:"must be string"}];
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
validate66.errors = [{instancePath,schemaPath:"#/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
validate66.errors = vErrors;
return errors === 0;
}
validate66.evaluated = {"props":true,"dynamicProps":false,"dynamicItems":false};

export const mark_read_output = validate67;
const schema96 = {"$schema":"https://json-schema.org/draft/2020-12/schema","additionalProperties":false,"properties":{"conversation":{"type":["string","null"]},"notice":{"type":["string","null"]}},"title":"Applied","type":"object"};

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
const _errs1 = errors;
for(const key0 in data){
if(!((key0 === "conversation") || (key0 === "notice"))){
validate67.errors = [{instancePath,schemaPath:"#/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key0},message:"must NOT have additional properties"}];
return false;
break;
}
}
if(_errs1 === errors){
if(data.conversation !== undefined){
let data0 = data.conversation;
const _errs2 = errors;
if((typeof data0 !== "string") && (data0 !== null)){
validate67.errors = [{instancePath:instancePath+"/conversation",schemaPath:"#/properties/conversation/type",keyword:"type",params:{type: schema96.properties.conversation.type},message:"must be string,null"}];
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
validate67.errors = [{instancePath:instancePath+"/notice",schemaPath:"#/properties/notice/type",keyword:"type",params:{type: schema96.properties.notice.type},message:"must be string,null"}];
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
validate67.errors = [{instancePath,schemaPath:"#/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
validate67.errors = vErrors;
return errors === 0;
}
validate67.evaluated = {"props":true,"dynamicProps":false,"dynamicItems":false};

export const mark_read_error = validate68;
const schema97 = {"$schema":"https://json-schema.org/draft/2020-12/schema","additionalProperties":false,"properties":{"code":{"type":"string"},"message":{"type":"string"}},"required":["code","message"],"title":"ChatError","type":"object"};

function validate68(data, {instancePath="", parentData, parentDataProperty, rootData=data, dynamicAnchors={}}={}){
let vErrors = null;
let errors = 0;
const evaluated0 = validate68.evaluated;
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
validate68.errors = [{instancePath,schemaPath:"#/required",keyword:"required",params:{missingProperty: missing0},message:"must have required property '"+missing0+"'"}];
return false;
}
else {
const _errs1 = errors;
for(const key0 in data){
if(!((key0 === "code") || (key0 === "message"))){
validate68.errors = [{instancePath,schemaPath:"#/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key0},message:"must NOT have additional properties"}];
return false;
break;
}
}
if(_errs1 === errors){
if(data.code !== undefined){
const _errs2 = errors;
if(typeof data.code !== "string"){
validate68.errors = [{instancePath:instancePath+"/code",schemaPath:"#/properties/code/type",keyword:"type",params:{type: "string"},message:"must be string"}];
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
validate68.errors = [{instancePath:instancePath+"/message",schemaPath:"#/properties/message/type",keyword:"type",params:{type: "string"},message:"must be string"}];
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
validate68.errors = [{instancePath,schemaPath:"#/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
validate68.errors = vErrors;
return errors === 0;
}
validate68.evaluated = {"props":true,"dynamicProps":false,"dynamicItems":false};

export const events_args = validate69;
const schema98 = {"$schema":"https://json-schema.org/draft/2020-12/schema","additionalProperties":false,"properties":{"after":{"type":"string"},"wait_ms":{"format":"uint16","maximum":65535,"minimum":0,"type":"integer"}},"required":["after","wait_ms"],"title":"ChatEventsArgs","type":"object"};

function validate69(data, {instancePath="", parentData, parentDataProperty, rootData=data, dynamicAnchors={}}={}){
let vErrors = null;
let errors = 0;
const evaluated0 = validate69.evaluated;
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
validate69.errors = [{instancePath,schemaPath:"#/required",keyword:"required",params:{missingProperty: missing0},message:"must have required property '"+missing0+"'"}];
return false;
}
else {
const _errs1 = errors;
for(const key0 in data){
if(!((key0 === "after") || (key0 === "wait_ms"))){
validate69.errors = [{instancePath,schemaPath:"#/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key0},message:"must NOT have additional properties"}];
return false;
break;
}
}
if(_errs1 === errors){
if(data.after !== undefined){
const _errs2 = errors;
if(typeof data.after !== "string"){
validate69.errors = [{instancePath:instancePath+"/after",schemaPath:"#/properties/after/type",keyword:"type",params:{type: "string"},message:"must be string"}];
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
validate69.errors = [{instancePath:instancePath+"/wait_ms",schemaPath:"#/properties/wait_ms/type",keyword:"type",params:{type: "integer"},message:"must be integer"}];
return false;
}
if(errors === _errs4){
if((typeof data1 == "number") && (isFinite(data1))){
if(data1 > 65535 || isNaN(data1)){
validate69.errors = [{instancePath:instancePath+"/wait_ms",schemaPath:"#/properties/wait_ms/maximum",keyword:"maximum",params:{comparison: "<=", limit: 65535},message:"must be <= 65535"}];
return false;
}
else {
if(data1 < 0 || isNaN(data1)){
validate69.errors = [{instancePath:instancePath+"/wait_ms",schemaPath:"#/properties/wait_ms/minimum",keyword:"minimum",params:{comparison: ">=", limit: 0},message:"must be >= 0"}];
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
validate69.errors = [{instancePath,schemaPath:"#/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
validate69.errors = vErrors;
return errors === 0;
}
validate69.evaluated = {"props":true,"dynamicProps":false,"dynamicItems":false};

export const events_output = validate70;
const schema99 = {"$schema":"https://json-schema.org/draft/2020-12/schema","title":"string","type":"string"};

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
if(typeof data !== "string"){
validate70.errors = [{instancePath,schemaPath:"#/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
validate70.errors = vErrors;
return errors === 0;
}
validate70.evaluated = {"dynamicProps":false,"dynamicItems":false};

export const events_error = validate71;
const schema100 = {"$schema":"https://json-schema.org/draft/2020-12/schema","additionalProperties":false,"properties":{"code":{"type":"string"},"message":{"type":"string"}},"required":["code","message"],"title":"ChatError","type":"object"};

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
if(((data.code === undefined) && (missing0 = "code")) || ((data.message === undefined) && (missing0 = "message"))){
validate71.errors = [{instancePath,schemaPath:"#/required",keyword:"required",params:{missingProperty: missing0},message:"must have required property '"+missing0+"'"}];
return false;
}
else {
const _errs1 = errors;
for(const key0 in data){
if(!((key0 === "code") || (key0 === "message"))){
validate71.errors = [{instancePath,schemaPath:"#/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key0},message:"must NOT have additional properties"}];
return false;
break;
}
}
if(_errs1 === errors){
if(data.code !== undefined){
const _errs2 = errors;
if(typeof data.code !== "string"){
validate71.errors = [{instancePath:instancePath+"/code",schemaPath:"#/properties/code/type",keyword:"type",params:{type: "string"},message:"must be string"}];
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
validate71.errors = [{instancePath:instancePath+"/message",schemaPath:"#/properties/message/type",keyword:"type",params:{type: "string"},message:"must be string"}];
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
validate71.errors = [{instancePath,schemaPath:"#/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
validate71.errors = vErrors;
return errors === 0;
}
validate71.evaluated = {"props":true,"dynamicProps":false,"dynamicItems":false};
