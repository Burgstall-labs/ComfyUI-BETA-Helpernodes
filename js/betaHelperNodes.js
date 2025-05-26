import { app } from "/scripts/app.js";

console.log("[BETA Helper Nodes] betaHelperNodes.js script loaded by browser.");

app.registerExtension({
    name: "Comfy.BETAHelperNodes.IndexedLoraLoaderLogic", // Unique name for your extension's JS part
    async nodeCreated(node) {
        // Log for *every* node created to see its type and title
        // console.log(`[BETA Helper Nodes] nodeCreated event: type = '${node.type}', title = '${node.title}'`);

        // --- WORKAROUND: Check title because node.type might be empty for some custom nodes ---
        // Make sure this title string EXACTLY matches your node's display name
        const expectedNodeTitle = "Indexed LoRA Loader 🎯 🅑🅔🅣🅐"; // Update if your display name is different!

        if (node.title === expectedNodeTitle) {
            console.log(`[BETA Helper Nodes] MATCHED node by TITLE: '${node.title}' (type was '${node.type}')`, node);

            const numberWidget = node.widgets.find(w => w.name === "number_of_loras");
            const indexWidget = node.widgets.find(w => w.name === "index");

            if (!numberWidget) {
                console.error("[BETA Helper Nodes] CRITICAL: Could not find 'number_of_loras' widget for node: " + node.title);
                return;
            }
            // console.log("[BETA Helper Nodes] Found 'number_of_loras' widget:", numberWidget);

            if (!indexWidget) {
                console.warn("[BETA Helper Nodes] Could not find 'index' widget for node: " + node.title + ". Index max won't be updated dynamically.");
            } else {
                // console.log("[BETA Helper Nodes] Found 'index' widget:", indexWidget);
            }

            const updateLoraWidgetsVisibility = () => {
                const numLorasRaw = numberWidget.value;
                const numLorasParsed = parseInt(numLorasRaw, 10);
                // Ensure validNumLoras is at least 1, default to 1 if parsing fails or value is < 1
                const validNumLoras = isNaN(numLorasParsed) || numLorasParsed < 1 ? 1 : numLorasParsed;

                // console.log(`[BETA Helper Nodes] updateLoraWidgetsVisibility called. number_of_loras = ${validNumLoras} (raw input: ${numLorasRaw})`);

                for (let i = 1; i <= 20; i++) { // Assuming max 20 lora slots as per Python
                    const loraWidgetName = `lora_${i}`;
                    const loraWidget = node.widgets.find(w => w.name === loraWidgetName);

                    if (loraWidget) {
                        let elementToHide = null;
                        // Try to find the most common parent elements that control widget visibility
                        if (loraWidget.inputEl) {
                            elementToHide = loraWidget.inputEl.closest("tr");
                            if (!elementToHide) elementToHide = loraWidget.inputEl.closest(".widget"); // Common general wrapper
                            if (!elementToHide) elementToHide = loraWidget.inputEl.closest("div"); // Fallback to any div
                            // If it's a combo box, its main input might be nested.
                            // The 'comfy-combo-wrapper' is often a good target if 'tr' or '.widget' isn't the direct parent of the wrapper.
                            if (loraWidget.inputEl.parentElement?.classList.contains("comfy-combo-wrapper")) {
                                let comboWrapper = loraWidget.inputEl.parentElement;
                                elementToHide = comboWrapper.closest("tr") || comboWrapper.closest(".widget") || comboWrapper;
                            }
                        } else if (loraWidget.canvas) { // For widgets that are primarily a canvas
                            elementToHide = loraWidget.canvas.closest("tr") || loraWidget.canvas.closest(".widget");
                        } else if (loraWidget.el) { // Some widgets might use 'el' for their root DOM element
                             elementToHide = loraWidget.el.closest("tr") || loraWidget.el.closest(".widget") || loraWidget.el;
                        }


                        if (elementToHide) {
                            const shouldBeVisible = (i <= validNumLoras);
                            elementToHide.style.display = shouldBeVisible ? "" : "none";
                            // console.log(`[BETA Helper Nodes] Widget ${loraWidgetName} (${elementToHide.tagName}.${elementToHide.className}) display set to: ${shouldBeVisible ? "visible" : "none"}`);
                        } else {
                            console.warn(`[BETA Helper Nodes] Could not find suitable DOM element to hide for widget: ${loraWidgetName}. Widget object:`, loraWidget);
                        }
                    }
                }

                // Update the 'index' widget's max value and current value if needed
                if (indexWidget) {
                    const newMax = Math.max(1, validNumLoras); // Max should be at least 1

                    if (indexWidget.options.max !== newMax) {
                        indexWidget.options.max = newMax;
                        // console.log(`[BETA Helper Nodes] Index widget options.max updated to: ${newMax}`);
                    }
                    // Also update the input element's max attribute if it exists (for browser validation)
                    if (indexWidget.inputEl && typeof indexWidget.inputEl.max !== 'undefined' && indexWidget.inputEl.max !== newMax.toString()) {
                        indexWidget.inputEl.max = newMax.toString();
                    }

                    let currentIndexValue = parseInt(indexWidget.value, 10);
                    const minVal = parseInt(indexWidget.options.min || 1, 10);
                    if(isNaN(currentIndexValue)) currentIndexValue = minVal; // Handle if current value is NaN

                    let clampedIndexValue = currentIndexValue;
                    if (clampedIndexValue > newMax) clampedIndexValue = newMax;
                    if (clampedIndexValue < minVal) clampedIndexValue = minVal;

                    if (indexWidget.value !== clampedIndexValue) {
                        indexWidget.value = clampedIndexValue;
                        // console.log(`[BETA Helper Nodes] Index widget value clamped/set to: ${clampedIndexValue}`);
                    }
                }
                node.computeSize(); // Important to tell LiteGraph to re-calculate the node's dimensions
                node.setDirtyCanvas(true, true); // Force a redraw of the canvas
            };

            // console.log("[BETA Helper Nodes] Calling updateLoraWidgetsVisibility initially for node: " + node.title);
            // A small timeout can sometimes help ensure widgets are fully initialized in the DOM before styling.
            setTimeout(updateLoraWidgetsVisibility, 100); // Increased timeout slightly

            // Store original callback if it exists, then wrap it
            const originalNumberCallback = numberWidget.callback;
            numberWidget.callback = (value) => {
                // console.log(`[BETA Helper Nodes] 'number_of_loras' widget callback triggered for node '${node.title}'. New raw value:`, value);
                // It's good practice to ensure the widget's internal value is updated if ComfyUI doesn't do it before the callback
                numberWidget.value = parseInt(value, 10); // Update widget's value, parseInt here
                if (isNaN(numberWidget.value)) numberWidget.value = 1; // Fallback if parsing fails

                if (originalNumberCallback) {
                    originalNumberCallback.call(numberWidget, numberWidget.value); // Pass the parsed value
                }
                updateLoraWidgetsVisibility();
            };
            // console.log("[BETA Helper Nodes] Callback attached to 'number_of_loras' widget for node: " + node.title);
        }
    }
});
