class VirtualList {
  constructor(containerClass, itemCount, itemHeight) {
    // wait until the reconciler has actually built the element
    const container = document.querySelector(`.${containerClass}`);
    if (!container) {
      console.warn(`VirtualList: container .${containerClass} not found`);
      return;
    }
    this.viewport = container.querySelector(".viewport");
    this.phantom  = container.querySelector(".phantom");
    this.itemCount = itemCount;
    this.itemHeight = itemHeight;

    this.phantom.style.height = this.itemCount * this.itemHeight + "px";
    this.viewport.addEventListener("scroll", () => this.render());
    this.render();
  }

  render() {
    const scrollTop = this.viewport.scrollTop;
    const viewportH = this.viewport.clientHeight;
    const start = Math.floor(scrollTop / this.itemHeight);
    const end   = Math.min(
      this.itemCount,
      Math.ceil((scrollTop + viewportH) / this.itemHeight)
    );

    // clear old rows
    this.viewport.querySelectorAll(".virtual-item").forEach(n => n.remove());

    // create placeholder divs – reconciler will patch the real content
    const frag = document.createDocumentFragment();
    for (let i = start; i < end; ++i) {
      const row = document.createElement("div");
      row.className = "virtual-item";
      row.style.position = "absolute";
      row.style.top = i * this.itemHeight + "px";
      row.style.left = 0;
      row.style.right = 0;
      row.style.height = this.itemHeight + "px";
      frag.appendChild(row);
    }
    this.viewport.appendChild(frag);
  }
}

window.VirtualList = VirtualList;