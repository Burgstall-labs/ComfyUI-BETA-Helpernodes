import { app } from "/scripts/app.js";

console.log("[BETA Helper Nodes] betaHelperNodes.js script loaded by browser.");

app.registerExtension({
    name: "Comfy.BETAHelperNodes.IndexedLoraLoaderLogic", // Slightly more descriptive name
    async nodeCreated(node) {
        // Log for *every* node created to see its type and title
        console.log(`[BETA Helper Nodes] nodeCreated event: type = '${node.type}', title = '${node.title}'`);

        // --- WORKAROUND: Check title because node.type is coming as empty ---
        // Make sure this title string EXACTLY matches what you see in the console log
        const expectedNodeTitle = "Indexed LoRA Loader 🎯 🅑🅔🅣🅐";

        if (node.title === expectedNodeTitle) {
            console.log(`[BETA Helper Nodes] MATCHED node by TITLE: '${node.title}' (type was '${node.type}')`, node);

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
                // Ensure numLoras is a valid number, default to 1 if not.
                const validNumLoras = isNaN(numLoras) ? 1 : numLoras;

                console.log(`[BETA Helper Nodes] updateLoraWidgetsVisibility called. number_of_loras = ${validNumLoras}`);

                for (let i = 1; i <= 20; i++) { // Assuming max 20 lora slots
                    const loraWidgetName = `lora_${i}`;
                    const loraWidget = node.widgets.find(w => w.name === loraWidgetName);
                    if (loraWidget) {
                        let elementToHide = loraWidget.inputEl;
                        if (elementToHide?.parentElement?.classList.contains("comfy-combo-wrapper")) {
                            elementToHide = elementToHide.parentElement;
                        }
                        // General approach: try to get the whole widget row/container
                        const widgetContainer = loraWidget.inputEl?.closest("tr") || loraWidget.inputEl?.closest(".widget");
                        if (widgetContainer) {
                           elementToHide = widgetContainer;
                        }


                        if (elementToHide) {
                            elementToHide.style.display = (i <= validNumLoras) ? "" : "none";
                        } else {
                            // console.warn(`[BETA Helper Nodes] Could not find suitable element to hide for ${loraWidgetName}`);
                        }
                    }
                }

                if (indexWidget) {
                    const newMax = validNumLoras > 0 ? validNumLoras : 1; // Max should be at least 1
                    if (indexWidget.options.max !== newMax) {
                        indexWidget.options.max = newMax;
                        if (indexWidget.inputEl) indexWidget.inputEl.max = newMax;
                        console.log(`[BETA Helper Nodes] Index widget max updated to: ${newMax}`);
                    }
                    if (indexWidget.value > newMax) {
                        indexWidget.value = newMax;
                        console.log(`[BETA Helper Nodes] Index widget value clamped to: ${newMax}`);
                    } else if (indexWidget.value < (indexWidget.options.min || 1) ) {
                        indexWidget.value = (indexWidget.options.min || 1); // Ensure min is respected
                    }
                }
                node.computeSize();
                node.setDirtyCanvas(true, true); // Use node's own method
            };

            console.log("[BETA Helper Nodes] Calling updateLoraWidgetsVisibility initially.");
            // It's possible widgets aren't fully initialized here yet.
            // A small timeout might be needed if initial hide doesn't work.
            setTimeout(updateLoraWidgetsVisibility, 50); // Small delay

            const originalNumberCallback = numberWidget.callback;
            numberWidget.callback = (value) => {
                console.log("[BETA Helper Nodes] 'number_of_loras' widget callback triggered. New value:", value);
                // ComfyUI usually updates numberWidget.value before the callback,
                // but ensure it's a number for our logic
                numberWidget.value = parseInt(value, 10);
                if (originalNumberCallback) {
                    originalNumberCallback.call(numberWidget, value);
                }
                updateLoraWidgetsVisibility();
            };
            console.log("[BETA Helper Nodes] Callback attached to 'number_of_loras' widget.");
        }
    }
});
