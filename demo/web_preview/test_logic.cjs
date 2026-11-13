// SPDX-License-Identifier: BSD-3-Clause
// Dependency-free model/event checks. This is NOT browser or visual verification.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

class Element {
  constructor(tag = 'div') {
    this.tagName = tag;
    this.children = [];
    this.value = '';
    this.checked = false;
    this.textContent = '';
    this._html = '';
    this._id = '';
    this.attributes = {};
    const classes = new Set();
    this.classList = {
      add: name => classes.add(name),
      remove: name => classes.delete(name),
      toggle: (name, force) => {
        const add = force === undefined ? !classes.has(name) : force;
        if (add) classes.add(name); else classes.delete(name);
        return add;
      },
      contains: name => classes.has(name),
    };
  }
  get id() { return this._id; }
  set id(value) {
    if (this._id && elements.get(this._id) === this) elements.delete(this._id);
    this._id = String(value);
    if (this._id) elements.set(this._id, this);
  }
  get innerHTML() { return this._html; }
  set innerHTML(value) { this.replaceChildren(); this._html = value; }
  append(...children) { this.children.push(...children); }
  replaceChildren(...children) {
    const remove = child => {
      if (child.id && elements.get(child.id) === child) elements.delete(child.id);
      if (document.activeElement === child) document.activeElement = document.body;
      for (const descendant of child.children || []) remove(descendant);
    };
    for (const child of this.children) remove(child);
    this.children = children;
  }
  setAttribute(key, value) {
    this.attributes[key] = String(value);
    if (key === 'id') this.id = value;
  }
  addEventListener(name, fn) { this['on' + name] = fn; }
  focus() { document.activeElement = this; }
}
const elements = new Map();
const document = {
  documentElement: {},
  body: new Element('body'),
  activeElement: null,
  getElementById(id) {
    return elements.get(id) || null;
  },
  createElement: tag => new Element(tag),
  createTextNode: text => ({textContent: text}),
};
const html = fs.readFileSync(path.join(__dirname, 'index.html'), 'utf8');
assert(!/<(?:script|link)[^>]+(?:src|href)\s*=\s*["']https?:/i.test(html), 'preview must not fetch external scripts or CSS');
for (const match of html.matchAll(/<[^>]*\bid="([^"]+)"[^>]*>/g)) {
  const element = new Element();
  element.id = match[1];
  const className = match[0].match(/\bclass="([^"]+)"/);
  if (className) for (const name of className[1].split(' ')) element.classList.add(name);
}
const script = html.match(/<script>([\s\S]*?)<\/script>/)[1];
const context = vm.createContext({document, setTimeout, clearTimeout, console});
new vm.Script(script).runInContext(context);
const run = source => vm.runInContext(source, context);

(async () => {
  let count = 0;
  const check = (condition, name) => { assert(condition, name); count++; console.log('PASS', name); };
  check(run("tags.length === 10 && countries.length === 10 && tags.every(t => words[t].length === keys.length)"), 'ten countries and complete primary UI label tables');
  run("$('region-cn:44').onclick(); $('region-cn:4403').onclick()");
  check(run("ids().join('/') === 'cc:CN/cn:44/cn:4403'"), 'deep selection produces complete ancestry');
  run("$('locale').onchange({target:{value:'ar'}})");
  check(document.documentElement.dir === 'rtl' && run("ids().join('/') === 'cc:CN/cn:44/cn:4403'"), 'Arabic applies RTL without changing IDs');
  run("$('confirm').onclick()");
  check(run("saved.datasetId === 'geo-regions-ui-fixture' && saved.pathIds.length === 3 && !dirty()"), 'confirmation emits fixture namespace and stable path');
  run("const confirmedSnapshot=saved; $('confirm').onclick()");
  check(run('saved === confirmedSnapshot && $("confirm").disabled'), 'unchanged confirmed selection cannot be submitted repeatedly');
  run("$('search').value='no-such-region-2398'; $('search').oninput()");
  check(elements.get('regions').children[0].children.some(e => e.textContent === run("tr('empty')")), 'missing search gives empty-result state');
  run("$('clear').onclick()");
  check(run('$("search").value === "" && $("region-cn:440305") !== null'), 'clear control restores the current level');
  run("$('back').onclick()");
  check(run("ids().join('/') === 'cc:CN/cn:44'"), 'back control removes exactly one draft level');
  run("$('discard').onclick()");
  check(run('$("app").inert && !$("dialog").classList.contains("hidden") && document.activeElement === $("keep")'), 'discard dialog isolates the background and focuses its safe action');
  run("$('dialog').onkeydown({key:'Tab',shiftKey:true,preventDefault(){}})");
  check(run('document.activeElement === $("discard-confirm")'), 'dialog Shift+Tab wraps to its last action');
  run("$('dialog').onkeydown({key:'Tab',shiftKey:false,preventDefault(){}})");
  check(run('document.activeElement === $("keep")'), 'dialog Tab wraps to its first action');
  run("$('dialog').onkeydown({key:'Escape',preventDefault(){}})");
  check(run('!$("app").inert && $("dialog").classList.contains("hidden") && path.length === 1'), 'Escape closes the dialog without discarding the draft');
  run("$('discard').onclick(); $('discard-confirm').onclick()");
  check(run("ids().join('/') === 'cc:CN/cn:44/cn:4403' && !dirty()"), 'discard confirmation restores the last confirmed selection');
  run("$('theme').onclick()");
  check(run('document.body.classList.contains("dark") && $("theme").attributes["aria-pressed"] === "true"'), 'theme control exposes its toggled state');
  run("for(const next of tags) $('locale').onchange({target:{value:next}})");
  check(run('locale === "ar" && ids().join("/") === "cc:CN/cn:44/cn:4403"'), 'all ten language controls preserve the draft path');
  run("$('offline').checked=true; $('country-JP').focus()");
  await run("$('country-JP').onclick()");
  check(run('document.activeElement === $("country-JP")'), 'rerender preserves focus on the selected country control');
  check(run('failed && !loading && !cached.has("JP")'), 'uncached country fails when offline');
  run("$('offline').checked=false");
  await run("$('retry').onclick()");
  check(run('!failed && cached.has("JP")'), 'retry recovers and caches downloaded fixture');
  run("$('offline').checked=true");
  await run("loadCountry('JP')");
  check(run('!failed && code === "JP"'), 'cached fixture remains available offline');
  run("$('offline').checked=false");
  await run("Promise.all([loadCountry('US'), loadCountry('CN')])");
  check(run('code === "CN" && !loading && !failed && !cached.has("US")'), 'obsolete request cannot overwrite country or mutate cache');
  run("$('fail').onclick()");
  check(run('failed && !loading'), 'failure scenario is reachable');
  await run("loadCountry('CN')");
  check(run('!failed && code === "CN"'), 'bundled fixture retries successfully');
  console.log(`${count} behavior checks passed. Layout, focus geometry and Flutter execution are NOT verified by this test.`);
})().catch(error => { console.error(error); process.exitCode = 1; });
