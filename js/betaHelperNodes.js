import { app } from "../../../scripts/app.js";

console.log("[BETA Helper Nodes] betaHelperNodes.js (v_add_remove) script loaded.");

app.registerExtension({
    name: "Comfy.BETAHelperNodes.IndexedLoraLoaderLogic",
    async nodeCreated(node) {
        const expectedNodeTitle = "Indexed LoRA Loader 🎯 🅑🅔🅣🅐"; // Ensure this matches your node's display name

        if (node.title === expectedNodeTitle) {
            console.log(`[BETA Helper Nodes] MATCHED node by TITLE: '${node.title}'`);

            // Initialize properties object if it doesn't exist (for storing widget values)
            if (!node.properties) {
                node.properties = {};
            }

            const updateDynamicWidgets = () => {
                const numLorasWidget = node.widgets.find(w => w.name === "number_of_loras");
                if (!numLorasWidget) {
                    console.error("[BETA Helper Nodes] 'number_of_loras' widget not found!");
                    return;
                }
                const numLoras = parseInt(numLorasWidget.value, 10) || 1; // Default to 1 if NaN or < 1

                const indexWidget = node.widgets.find(w => w.name === "index");

                // --- 1. Save current values of all dynamic and related static widgets ---
                // We only need to save lora_X values, as others are part of required_inputs or static optionals
                for (let i = 1; i <= 20; i++) { // Max possible loras
                    const loraWidget = node.widgets.find(w => w.name === `lora_${i}`);
                    if (loraWidget) {
                        node.properties[`lora_${i}`] = loraWidget.value;
                    }
                }
                if (indexWidget) { // Save index widget value
                    node.properties["index"] = indexWidget.value;
                }


                // --- 2. Remove existing lora_X widgets ---
                // Keep track of widgets that are NOT lora_X to re-add them in order
                const staticWidgets = node.widgets.filter(w => !w.name.startsWith("lora_"));
                node.widgets = [...staticWidgets]; // Temporarily set widgets to non-lora ones

                // --- 3. Re-add lora_X widgets based on numLoras ---
                const loraListSourceWidget = staticWidgets.find(w => w.name === "lora_1_source_for_options"); // A bit of a hack: assume lora_1 (if it existed) had the list
                                                                                                           // Or get it from the first lora_X if any exist before removal
                let loraOptionsList = ["none"]; // Default if no source found
                if(node.widgets_values && node.widgets_values["lora_1"]){ // if lora_1 has values
                    loraOptionsList = node.widgets.find(w=>w.name === "lora_1")?.options?.values || node.widgets_values["lora_1"];
                } else { // Fallback: try to get from python definition if possible (hard without direct access here)
                    // This is tricky; usually, the Python side defines this.
                    // For now, we'll use a simple ["none"] or try to grab from an existing lora_1 if it was there.
                    // Best practice: the Python node should provide these options if they can change.
                    // If your lora list is static from Python, this part is simpler.
                    // We assume the options list is the same for all lora_X dropdowns.
                    const anExistingLoraWidget = node.widgets.find(w => w.name === "lora_1" && w.options && w.options.values);
                    if (anExistingLoraWidget) {
                        loraOptionsList = anExistingLoraWidget.options.values;
                    }
                }


                for (let i = 1; i <= numLoras; i++) {
                    const loraWidgetName = `lora_${i}`;
                    const savedValue = node.properties[loraWidgetName];
                    const defaultValue = loraOptionsList.includes(savedValue) ? savedValue : loraOptionsList[0] || "none";

                    node.addWidget(
                        "combo",
                        loraWidgetName,
                        defaultValue,
                        (value) => { node.properties[loraWidgetName] = value; }, // Save on change
                        { values: loraOptionsList }
                    );
                }

                // --- 4. Update Index Widget Max ---
                if (indexWidget) {
                    const newMax = Math.max(1, numLoras);
                    indexWidget.options.max = newMax;
                    if (indexWidget.inputEl && typeof indexWidget.inputEl.max !== 'undefined') {
                        indexWidget.inputEl.max = newMax.toString();
                    }
                    let currentIndexValue = parseInt(indexWidget.value, 10);
                    const minVal = parseInt(indexWidget.options.min || 1, 10);
                    if(isNaN(currentIndexValue)) currentIndexValue = minVal;

                    let clampedIndexValue = currentIndexValue;
                    if (clampedIndexValue > newMax) clampedIndexValue = newMax;
                    if (clampedIndexValue < minVal) clampedIndexValue = minVal;

                    if (indexWidget.value !== clampedIndexValue) {
                        indexWidget.value = clampedIndexValue;
                    }
                }

                // --- 5. Finalize ---
                node.computeSize();
                node.setDirtyCanvas(true, true);
            };

            // Initial setup and when number_of_loras changes
            const numLorasWidget = node.widgets.find(w => w.name === "number_of_loras");
            if (numLorasWidget) {
                const originalCallback = numLorasWidget.callback;
                numLorasWidget.callback = (value) => {
                    numLorasWidget.value = parseInt(value, 10); // Ensure internal value is number
                    if (originalCallback) originalCallback.call(numLorasWidget, numLorasWidget.value);
                    updateDynamicWidgets();
                };
            }

            // Handle Graph/Node Deserialization (loading a saved workflow)
            const onNodeConfigure = node.onConfigure;
            node.onConfigure = function(info) {
                if (onNodeConfigure) onNodeConfigure.apply(this, arguments);
                if (this.properties) { // Restore saved properties
                    // Values for lora_X might be in widgets_values if saved that way
                    if (info.widgets_values) {
                        for (let i = 1; i <= 20; i++) {
                            const loraWidgetName = `lora_${i}`;
                            if (info.widgets_values[loraWidgetName] !== undefined) {
                                this.properties[loraWidgetName] = info.widgets_values[loraWidgetName];
                            }
                        }
                    }
                }
                // console.log("[BETA Helper Nodes] onConfigure, properties:", this.properties);
                setTimeout(updateDynamicWidgets, 50); // Update widgets after configuration
            };
            
            // Save widget values correctly for serialization
            // ComfyUI usually serializes widget.value from node.widgets_values automatically
            // But we need to ensure our node.properties are also considered if they hold the true state.
            // The Bjornulf node does more explicit properties saving onSerialize.
            // For now, let's rely on ComfyUI's default widget_values serialization
            // and restore from node.properties if widgets_values aren't there on load.

            // Initial call
            setTimeout(updateDynamicWidgets, 100); // Delay slightly for everything to be ready
        }
    }
});
