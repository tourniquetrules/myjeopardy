(function () {
  "use strict";

  function isHtmlString(s) {
    return typeof s === "string" && s.trim().startsWith("<") && s.trim().endsWith(">");
  }

  function createFromHtml(html) {
    const template = document.createElement("template");
    template.innerHTML = html.trim();
    const nodes = Array.from(template.content.childNodes).filter((n) => n.nodeType === Node.ELEMENT_NODE);
    return nodes;
  }

  class MiniQuery {
    constructor(elements) {
      this.elements = elements || [];
    }

    _each(fn) {
      this.elements.forEach((el, idx) => fn(el, idx));
      return this;
    }

    empty() {
      return this._each((el) => {
        el.innerHTML = "";
      });
    }

    append(content) {
      const appendOne = (parent, item) => {
        if (item == null) return;

        if (item instanceof MiniQuery) {
          item.elements.forEach((child) => parent.appendChild(child));
          return;
        }

        if (item instanceof Node) {
          parent.appendChild(item);
          return;
        }

        if (typeof item === "string") {
          parent.insertAdjacentHTML("beforeend", item);
          return;
        }
      };

      return this._each((el) => appendOne(el, content));
    }

    text(value) {
      if (value === undefined) {
        return this.elements[0] ? this.elements[0].textContent : "";
      }
      return this._each((el) => {
        el.textContent = String(value);
      });
    }

    html(value) {
      if (value === undefined) {
        return this.elements[0] ? this.elements[0].innerHTML : "";
      }
      return this._each((el) => {
        el.innerHTML = String(value);
      });
    }

    show() {
      return this._each((el) => {
        el.style.display = "";
      });
    }

    hide() {
      return this._each((el) => {
        el.style.display = "none";
      });
    }

    css(prop, value) {
      if (value === undefined) {
        // Getter
        const el = this.elements[0];
        if (!el) return "";
        return getComputedStyle(el).getPropertyValue(prop);
      }

      return this._each((el) => {
        el.style[prop] = String(value);
      });
    }

    prop(name, value) {
      if (value === undefined) {
        const el = this.elements[0];
        return el ? el[name] : undefined;
      }
      return this._each((el) => {
        el[name] = value;
      });
    }

    attr(name, value) {
      if (value === undefined) {
        const el = this.elements[0];
        return el ? el.getAttribute(name) : null;
      }
      return this._each((el) => {
        el.setAttribute(name, String(value));
      });
    }

    val(value) {
      const el = this.elements[0];
      if (!el) return value === undefined ? "" : this;

      if (value === undefined) {
        return "value" in el ? el.value : "";
      }

      return this._each((e) => {
        if ("value" in e) e.value = value;
      });
    }

    on(eventName, handler) {
      return this._each((el) => {
        el.addEventListener(eventName, handler);
      });
    }

    click(handler) {
      return this.on("click", handler);
    }

    addClass(classNames) {
      const parts = String(classNames || "").split(/\s+/).filter(Boolean);
      return this._each((el) => {
        parts.forEach((c) => el.classList.add(c));
      });
    }

    removeClass(classNames) {
      const parts = String(classNames || "").split(/\s+/).filter(Boolean);
      return this._each((el) => {
        parts.forEach((c) => el.classList.remove(c));
      });
    }

    filter(fn) {
      const filtered = this.elements.filter((el, idx) => !!fn.call(el, idx, el));
      return new MiniQuery(filtered);
    }
  }

  function $(selectorOrHtmlOrElement) {
    if (selectorOrHtmlOrElement instanceof MiniQuery) return selectorOrHtmlOrElement;

    if (typeof selectorOrHtmlOrElement === "string") {
      if (isHtmlString(selectorOrHtmlOrElement)) {
        return new MiniQuery(createFromHtml(selectorOrHtmlOrElement));
      }
      return new MiniQuery(Array.from(document.querySelectorAll(selectorOrHtmlOrElement)));
    }

    if (selectorOrHtmlOrElement instanceof Node) {
      return new MiniQuery([selectorOrHtmlOrElement]);
    }

    return new MiniQuery([]);
  }

  window.$ = window.$ || $;
})();
