(function () {
  "use strict";

  const HOTKEY = "s";
  const ROOT_ID = "emoji-frequency-plot";
  const REGISTRY_KEY = "__emojiExplorerAltSHotkeyRegistered";
  const HOVER_STATE_KEY = "__emojiExplorerHoverLayerState";
  const HOVER_HOOK_KEY = "__emojiExplorerHoverHookAttached";
  const HOVER_OBSERVER_KEY = "__emojiExplorerHoverObserverRegistered";
  const HOVER_GRACE_MS = 1200;

  function getHoverState() {
    if (!window[HOVER_STATE_KEY]) {
      window[HOVER_STATE_KEY] = {
        layer: null,
        timestamp: 0,
        hovering: false,
        points: null,
      };
    }
    return window[HOVER_STATE_KEY];
  }

  function buildFilename(extension) {
    const now = new Date();
    const date = now.toISOString().replace(/[:]/g, "-").replace(/\..+$/, "");
    return `emoji-view-${date}.${extension}`;
  }

  function downloadBlob(blob, filename) {
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(link.href);
  }

  function hasHoverContent(hoverLayer) {
    if (!hoverLayer) {
      return false;
    }
    return Boolean(hoverLayer.querySelector(".hovertext, .spikeline, text"));
  }

  function recordHoverLayer(plotElement, eventData) {
    const state = getHoverState();
    const hoverLayer = plotElement.querySelector("svg.main-svg g.hoverlayer");
    if (hasHoverContent(hoverLayer)) {
      state.layer = hoverLayer.cloneNode(true);
      state.timestamp = Date.now();
      state.hovering = true;
    }

    if (eventData && Array.isArray(eventData.points)) {
      const points = eventData.points
        .map((point) => ({
          curveNumber: point.curveNumber,
          pointNumber:
            typeof point.pointNumber === "number"
              ? point.pointNumber
              : point.pointIndex,
        }))
        .filter(
          (point) =>
            typeof point.curveNumber === "number" &&
            typeof point.pointNumber === "number"
        );

      if (points.length > 0) {
        state.points = points;
        state.timestamp = Date.now();
      }
    }
  }

  function ensureHoverTracking(plotElement) {
    if (plotElement[HOVER_HOOK_KEY]) {
      return;
    }

    if (typeof plotElement.on === "function") {
      plotElement.on("plotly_hover", (eventData) =>
        recordHoverLayer(plotElement, eventData)
      );
      plotElement.on("plotly_unhover", () => {
        getHoverState().hovering = false;
      });
    }

    plotElement.addEventListener("mouseleave", () => {
      getHoverState().hovering = false;
    });

    plotElement[HOVER_HOOK_KEY] = true;
  }

  function attachHoverTrackingToCurrentPlot() {
    const graphRoot = document.getElementById(ROOT_ID);
    if (!graphRoot) {
      return;
    }

    const plotElement = graphRoot.querySelector(".js-plotly-plot");
    if (!plotElement) {
      return;
    }

    ensureHoverTracking(plotElement);
  }

  function observePlotMounts() {
    if (window[HOVER_OBSERVER_KEY]) {
      return;
    }

    attachHoverTrackingToCurrentPlot();

    const observer = new MutationObserver(() => {
      attachHoverTrackingToCurrentPlot();
    });
    observer.observe(document.documentElement, {
      childList: true,
      subtree: true,
    });
    window[HOVER_OBSERVER_KEY] = true;
  }

  function nextAnimationFrame() {
    return new Promise((resolve) => window.requestAnimationFrame(() => resolve()));
  }

  async function cloneHoverLayerForExport(plotElement) {
    const currentHoverLayer = plotElement.querySelector("svg.main-svg g.hoverlayer");
    if (hasHoverContent(currentHoverLayer)) {
      return currentHoverLayer.cloneNode(true);
    }

    const state = getHoverState();
    const freshEnough = Date.now() - state.timestamp <= HOVER_GRACE_MS;
    if (
      state.points &&
      freshEnough &&
      window.Plotly &&
      window.Plotly.Fx &&
      typeof window.Plotly.Fx.hover === "function"
    ) {
      window.Plotly.Fx.hover(plotElement, state.points);
      await nextAnimationFrame();
      const rebuiltHoverLayer = plotElement.querySelector("svg.main-svg g.hoverlayer");
      if (hasHoverContent(rebuiltHoverLayer)) {
        return rebuiltHoverLayer.cloneNode(true);
      }
    }

    if (state.layer && (state.hovering || freshEnough)) {
      return state.layer.cloneNode(true);
    }

    return null;
  }

  function injectHoverLayer(svgText, hoverLayer) {
    if (!hoverLayer) {
      return svgText;
    }

    const parser = new DOMParser();
    const svgDoc = parser.parseFromString(svgText, "image/svg+xml");
    const root = svgDoc.documentElement;
    if (!root || root.nodeName.toLowerCase() !== "svg") {
      return svgText;
    }

    const existingHoverLayer = root.querySelector("g.hoverlayer");
    if (existingHoverLayer) {
      existingHoverLayer.remove();
    }

    const importedHoverLayer = svgDoc.importNode(hoverLayer, true);
    root.appendChild(importedHoverLayer);
    return new XMLSerializer().serializeToString(root);
  }

  async function exportAsSvg(plotElement, width, height) {
    const hoverLayer = await cloneHoverLayerForExport(plotElement);
    const svgDataUrl = await window.Plotly.toImage(plotElement, {
      format: "svg",
      width,
      height,
    });
    const svgText = await (await fetch(svgDataUrl)).text();
    const svgWithHover = injectHoverLayer(svgText, hoverLayer);
    return new Blob([svgWithHover], { type: "image/svg+xml;charset=utf-8" });
  }

  async function exportAsHighResPng(plotElement, width, height) {
    const pngDataUrl = await window.Plotly.toImage(plotElement, {
      format: "png",
      width,
      height,
      scale: 3,
    });
    return (await fetch(pngDataUrl)).blob();
  }

  async function saveCurrentFigureView() {
    const graphRoot = document.getElementById(ROOT_ID);
    if (!graphRoot) {
      return;
    }

    const plotElement = graphRoot.querySelector(".js-plotly-plot");
    if (!plotElement || !window.Plotly || typeof window.Plotly.toImage !== "function") {
      return;
    }

    ensureHoverTracking(plotElement);

    const width = Math.max(1, Math.round(plotElement.clientWidth));
    const height = Math.max(1, Math.round(plotElement.clientHeight));

    try {
      const svgBlob = await exportAsSvg(plotElement, width, height);
      downloadBlob(svgBlob, buildFilename("svg"));
    } catch (svgError) {
      try {
        const pngBlob = await exportAsHighResPng(plotElement, width, height);
        downloadBlob(pngBlob, buildFilename("png"));
      } catch (pngError) {
        console.error("Could not export figure with Alt+S", svgError, pngError);
      }
    }
  }

  function onKeyDown(event) {
    if (!event.altKey || event.ctrlKey || event.metaKey || event.shiftKey) {
      return;
    }

    if (String(event.key || "").toLowerCase() !== HOTKEY) {
      return;
    }

    event.preventDefault();
    void saveCurrentFigureView();
  }

  if (!window[REGISTRY_KEY]) {
    observePlotMounts();
    window.addEventListener("keydown", onKeyDown);
    window[REGISTRY_KEY] = true;
  }
})();
