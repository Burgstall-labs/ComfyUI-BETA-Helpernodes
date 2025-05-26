import { app } from "/scripts/app.js";

console.log("[BETA Helper Nodes] betaHelperNodes.js script loaded by browser.");

app.registerExtension({
    name: "Comfy.BETAHelperNodes.IndexedLoraLoader", // Unique name for your extension's JS part
    async nodeCreated(node) {
        // Log every node creation to see if this function is even being called
        // console.log(`[BETA Helper Nodes] nodeCreated: type = ${node.type}, title = ${node.title}`);

        if (node.type === "IndexedLoRALoader_BETA") { // <<< CRITICAL: Must match NODE_CLASS_MAPPINGS key
            console.log("[BETA Helper Nodes] MATCHED IndexedLoRALoader_BETA node:", node);

            const numberWidget = node.widgets.find(w => w.name === "number_of_loras");
            const indexWidget = node.widgets.find(w => w.name === "index");

            if (!numberWidget) {
                console.error("[BETA Helper Nodes] CRITICAL: Could not find 'number_of_loras' widget.");
                return;
            }
            console.log("[BETA Helper Nodes] Found 'number_of_loras' widget:", numberWidget);

            if (!indexWidget) {
                console.warn("[BETA Helper Nodes] Could not find 'index' widget. Index max won't be updated.");
            } else {
                console.log("[BETA Helper Nodes] Found 'index' widget:", indexWidget);
            }

            const updateLoraWidgetsVisibility = () => {
                const numLoras = parseInt(numberWidget.value, 10);
                console.log(`[BETA Helper Nodes] updateLoraWidgetsVisibility called. number_of_loras = ${numLoras}`);

                for (let i = 1; i <= 20; i++) { // Assuming max 20 lora slots
                    const loraWidgetName = `lora_${i}`;
                    const loraWidget = node.widgets.find(w => w.name === loraWidgetName);
                    if (loraWidget) {
                        // Try to find the outermost element of the widget for hiding
                        let elementToHide = loraWidget.inputEl; // Start with inputEl
                        if (elementToHide && elementToHide.parentElement && elementToHide.parentElement.classList.contains("comfy-combo-wrapper")) {
                            elementToHide = elementToHide.parentElement; // For combo, hide wrapper
                        }
                        if (elementToHide && elementToHide.parentElement && elementToHide.parentElement.tagName === "TR") {
                            elementToHide = elementToHide.parentElement; // Often widgets are in table rows
                        } else if (elementToHide && elementToHide.closest) { // General fallback to find a TR or a common widget wrapper
                             let commonParent = elementToHide.closest(".widget") || elementToHide.closest("tr");
                             if(commonParent) elementToHide = commonParent;
                        }


                        if (elementToHide) {
                            elementToHide.style.display = (i <= numLoras) ? "" : "none";
                            // console.log(`[BETA Helper Nodes] Widget ${loraWidgetName} display set to: ${(i <= numLoras) ? "visible" : "none"}`);
                        } else {
                            console.warn(`[BETA Helper Nodes] Could not find suitable element to hide for ${loraWidgetName}`);
                        }
                    } else {
                        // console.warn(`[BETA Helper Nodes] Widget ${loraWidgetName} not found.`);
                    }
                }

                if (indexWidget) {
                    const currentMax = parseInt(indexWidget.options?.max || indexWidget.inputEl?.max || numLoras);
                    if (currentMax !== numLoras) {
                         indexWidget.options.max = numLoras;
                         if (indexWidget.inputEl) indexWidget.inputEl.max = numLoras;
                         console.log(`[BETA Helper Nodes] Index widget max updated to: ${numLoras}`);
                    }
                    if (indexWidget.value > numLoras) {
                        indexWidget.value = numLoras; // Clamp current value
                        console.log(`[BETA Helper Nodes] Index widget value clamped to: ${numLoras}`);
                    }
                }
                node.computeSize(); // Tell ComfyUI to recompute the node's size
                app.graph.setDirtyCanvas(true, true); // Redraw the graph
            };

            // Initial call
            console.log("[BETA Helper Nodes] Calling updateLoraWidgetsVisibility initially.");
            updateLoraWidgetsVisibility();

            // Store original callback if it exists, then wrap it
            const originalNumberCallback = numberWidget.callback;
            numberWidget.callback = (value) => {
                console.log("[BETA Helper Nodes] 'number_of_loras' widget callback triggered. New value:", value);
                if (originalNumberCallback) {
                    originalNumberCallback.call(numberWidget, value);
                }
                // Ensure numberWidget.value is updated before calling our logic if ComfyUI doesn't do it immediately
                // numberWidget.value = parseInt(value,10); // Usually ComfyUI handles this.
                updateLoraWidgetsVisibility();
            };
            console.log("[BETA Helper Nodes] Callback attached to 'number_of_loras' widget.");
        }
    }
});
