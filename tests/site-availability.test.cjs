const {test}=require('node:test');
const assert=require('node:assert/strict');
const {isPublishedPath}=require('../site-availability.js');
test('published files and directory indexes open normally',()=>{const paths=['index.html','docs/index.html','dashboard.js'];assert.ok(isPublishedPath('',paths));assert.ok(isPublishedPath('docs/',paths));assert.ok(isPublishedPath('dashboard.js',paths));});
test('private local folders do not masquerade as published files',()=>assert.equal(isPublishedPath('Family/Health/index.html',['index.html']),false));
