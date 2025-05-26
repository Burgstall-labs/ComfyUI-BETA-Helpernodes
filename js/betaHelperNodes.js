import { app } from "/scripts/app.js";

console.log("[BETA Helper Nodes] betaHelperNodes.js script loaded by browser.");

app.registerExtension({
    name: "Comfy.BETAHelperNodes.IndexedLoraLoader",
    async nodeCreated(node) {
        // Log for *every* node created to see its type
        console.log(`[BETA Helper Nodes] nodeCreated event: type = '${node.type}', title = '${node.title}'`);

        if (node.type === "IndexedLoRALoader_BETA") { // <<< Ensure this string is IDENTICAL to your Python NODE_CLASS_MAPPINGS key
            console.log("[BETA Helper Nodes] MATCHED IndexedLoRALoader_BETA node:", node);

            // ... rest of your code from the previous heavily logged version
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
                        let elementToHide = loraWidget.inputEl; 
                        if (elementToHide && elementToHide.parentElement && elementToHide.parentElement.classList.contains("comfy-combo-wrapper")) {
                            elementToHide = elementToHide.parentElement; 
                        }
                        if (elementToHide && elementToHide.parentElement && elementToHide.parentElement.tagName === "TR") {
                            elementToHide = elementToHide.parentElement; 
                        } else if (elementToHide && elementToHide.closest) { 
                            let commonParent = elementToHide.closest(".widget") || elementToHide.closest("tr");
                            if(commonParent) elementToHide = commonParent;
                        }

                        if (elementToHide) {
                            elementToHide.style.display = (i <= numLoras) ? "" : "none";
                        } else {
                            // console.warn(`[BETA Helper Nodes] Could not find suitable element to hide for ${loraWidgetName}`);
                        }
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
                        indexWidget.value = numLoras; 
                        console.log(`[BETA Helper Nodes] Index widget value clamped to: ${numLoras}`);
                    }
                }
                node.computeSize(); 
                app.graph.setDirtyCanvas(true, true); 
            };

            console.log("[BETA Helper Nodes] Calling updateLoraWidgetsVisibility initially.");
            updateLoraWidgetsVisibility();

            const originalNumberCallback = numberWidget.callback;
            numberWidget.callback = (value) => {
                console.log("[BETA Helper Nodes] 'number_of_loras' widget callback triggered. New value:", value);
                if (originalNumberCallback) {
                    originalNumberCallback.call(numberWidget, value);
                }
                updateLoraWidgetsVisibility();
            };
            console.log("[BETA Helper Nodes] Callback attached to 'number_of_loras' widget.");
        }
    }
});
