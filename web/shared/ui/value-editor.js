/** Create recursively labelled, repeatable controls for public nested API values.
 * When experiment configuration mounts, this editor preserves scalar types and
 * optional values so the operator never needs to write a JSON request document.
 */
export function createValueEditor(schema, title, initial) {
  const element = document.createElement('fieldset');
  element.className = 'value-editor';
  const legend = document.createElement('legend');
  legend.textContent = title;
  element.append(legend);
  const editor = node(schema, title, initial);
  element.append(editor.element);
  return { element, value: editor.value };
}

function node(schema, title, initial) {
  if (schema.type === 'object') {
    const element = document.createElement('div');
    element.className = 'field-grid';
    const children = schema.fields.map((field) => {
      const editor = node(field.schema, label(field.name), initial?.[field.name] ?? field.default);
      element.append(editor.element);
      return [field.name, editor];
    });
    return { element, value: () => Object.fromEntries(children.map(([name, editor]) => [name, editor.value()])) };
  }
  if (schema.type === 'optional') {
    const element = document.createElement('div');
    const enabled = document.createElement('input');
    enabled.type = 'checkbox';
    enabled.checked = initial !== undefined && initial !== null;
    const toggle = document.createElement('label');
    toggle.append(enabled, document.createTextNode(` Include ${title.toLowerCase()}`));
    const editor = node(schema.value, title, initial);
    const update = () => {
      editor.element.hidden = !enabled.checked;
      for (const control of editor.element.matches('input,select') ? [editor.element] : editor.element.querySelectorAll('input,select')) control.disabled = !enabled.checked;
    };
    enabled.addEventListener('change', update);
    element.append(toggle, editor.element);
    update();
    return {element, value: () => enabled.checked ? editor.value() : null};
  }
  if (schema.type === 'array') {
    const element = document.createElement('section');
    element.className = 'repeatable-editor';
    const heading = document.createElement('h4');
    heading.textContent = title;
    const list = document.createElement('div');
    const add = document.createElement('button');
    add.type = 'button';
    const singular = singularTitle(title);
    add.textContent = `Add ${singular.toLowerCase()}`;
    const children = [];
    let sequence = 0;
    function append(value) {
      const name = `${singular} ${++sequence}`;
      const editor = createValueEditor(schema.item, name, value);
      const remove = document.createElement('button');
      remove.type = 'button';
      remove.textContent = `Remove ${name.toLowerCase()}`;
      remove.addEventListener('click', () => {
        children.splice(children.indexOf(editor), 1);
        editor.element.remove();
        add.focus();
      });
      editor.element.append(remove);
      children.push(editor);
      list.append(editor.element);
    }
    add.addEventListener('click', () => append(undefined));
    for (const value of initial ?? []) append(value);
    element.append(heading, list, add);
    return {element, value: () => children.map((editor) => editor.value())};
  }
  if (schema.type === 'tuple') {
    const element = document.createElement('div');
    const editors = schema.items.map((item, index) => node(item, `${title} ${index + 1}`, initial?.[index]));
    element.append(...editors.map((editor) => editor.element));
    return { element, value: () => editors.map((editor) => editor.value()) };
  }
  if (schema.type === 'value') {
    const element = document.createElement('div');
    const type = document.createElement('select');
    type.setAttribute('aria-label', `${title} value type`);
    for (const name of ['string','integer','boolean','array']) type.add(new Option(name, name));
    let editor;
    const holder = document.createElement('div');
    function update() {
      editor = node(type.value === 'array' ? {type:'array',item:{type:'value'}} : {type:type.value}, title, undefined);
      holder.replaceChildren(editor.element);
    }
    type.addEventListener('change', update);
    update();
    element.append(type, holder);
    return {element, value: () => editor.value()};
  }
  const element = document.createElement('label');
  element.textContent = title;
  const control = document.createElement(schema.type === 'enum' ? 'select' : 'input');
  control.setAttribute('aria-label', title);
  if (schema.type === 'enum') {
    for (const value of schema.values) control.add(new Option(value, value));
    if (initial !== undefined) control.value = initial;
  } else if (schema.type === 'boolean') {
    control.type = 'checkbox';
    control.checked = initial ?? false;
  } else {
    control.type = schema.type === 'integer' || schema.type === 'decimal' ? 'number' : 'text';
    control.required = true;
    if (control.type === 'number') {
      if (schema.type === 'decimal') control.min = '0';
      control.step = schema.type === 'integer' ? '1' : 'any';
    }
    control.value = initial === undefined ? '' : String(initial);
  }
  element.append(control);
  return {element, value: () => {
    if (!control.checkValidity()) {
      control.reportValidity();
      throw new Error(`Complete the ${title.toLowerCase()} field before creating the run.`);
    }
    return schema.type === 'boolean' ? control.checked : schema.type === 'integer' ? Number(control.value) : control.value;
  }};
}

function label(name) {
  return name.replaceAll('_', ' ').replace(/\bid\b/g, 'ID').replace(/^./, (character) => character.toUpperCase());
}

function singularTitle(title) {
  const names = {Missions:'Mission', Ships:'Ship', Availabilities:'Availability', Rfqs:'RFQ', Quotes:'Quote', Offers:'Offer', Revisions:'Revision', 'Quote history':'Quote history entry', Requests:'Request', History:'History entry', 'Response rules':'Response rule', 'Availability changes':'Availability change', 'Communication profiles':'Communication profile', 'Loss rule':'Lost request ordinal', 'Duplication rule':'Duplicated request ordinal', 'Reordering rule':'Reordered request ordinal'};
  return names[title] ?? `${title} entry`;
}
