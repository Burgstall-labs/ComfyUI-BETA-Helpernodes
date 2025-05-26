import { app } from "../../../scripts/app.js";

console.log("[BETA Helper Nodes] betaHelperNodes.js (v_add_remove_resize) script loaded.");

app.registerExtension({
    name: "Comfy.BETAHelperNodes.IndexedLoraLoaderLogic",
    async nodeCreated(node) {
        const expectedNodeTitle = "Indexed LoRA Loader 🎯 🅑🅔🅣🅐"; // Ensure this matches your node's display name

        if (node.title === expectedNodeTitle) {
            console.log(`[BETA Helper Nodes] MATCHED node by TITLE: '${node.title}'`);

            if (!node.properties) {
                node.properties = {};
            }

            const updateDynamicWidgets = () => {
                const numLorasWidget = node.widgets.find(w => w.name === "number_of_loras");
                if (!numLorasWidget) {
                    console.error("[BETA Helper Nodes] 'number_of_loras' widget not found!");
                    return;
                }
                const numLoras = parseInt(numLorasWidget.value, 10) || 1;

                const indexWidget = node.widgets.find(w => w.name === "index");

                for (let i = 1; i <= 20; i++) {
                    const loraWidget = node.widgets.find(w => w.name === `lora_${i}`);
                    if (loraWidget) {
                        node.properties[`lora_${i}`] = loraWidget.value;
                    }
                }
                if (indexWidget) {
                    node.properties["index"] = indexWidget.value;
                }

                const staticWidgets = node.widgets.filter(w => !w.name.startsWith("lora_"));
                node.widgets = [...staticWidgets];

                let loraOptionsList = ["none"];
                const firstLoraWidgetInProperties = node.properties["lora_1"]; // Check if a value was saved
                // Try to get options from a previously existing lora_1 if its definition is in node.widgets_values
                // This part is heuristic as JS doesn't re-run Python INPUT_TYPES.
                // If you have access to the original widget definition somehow, that's better.
                if (node.widgets_values && node.widgets_values["lora_1"] && Array.isArray(node.widgets_values["lora_1"])) {
                    // This case is unlikely; widgets_values usually stores the *selected value*, not the options list.
                    // loraOptionsList = node.widgets_values["lora_1"];
                } else {
                    // Fallback: Check if the Python side somehow made options available on the node object
                    // or if we can find a template widget that defines them.
                    // This is often the hardest part for fully dynamic JS widgets if options are defined in Python.
                    // For now, we assume 'none' or a fixed list if not inferable.
                    // A common pattern is to have a hidden widget or property that stores the original options list.
                }
                // If your LoRA list is populated from folder_paths.get_filename_list("loras") in Python,
                // that list isn't directly available here. The options for the *combo* widget are set
                // when node.addWidget is called. If it's the first time, we need a source for `loraOptionsList`.
                // If `lora_X` widgets are defined in `optional_inputs` in Python, their initial options
                // are set there. We need to preserve/reuse those.
                // Let's assume for now `loraOptionsList` should be derived from the node's initial config if possible
                // or a fixed default. The Bjornulf code did:
                // const loraList = node.widgets.find(w => w.name === "lora_1")?.options?.values || [];
                // This implies lora_1 must exist or have existed to get its options.
                // We can try:
                const anExistingLoraWidgetBeforeRemoval = node.constructor.nodeData?.widgets?.find(w => w.name === "lora_1"); // Check original node data
                if(anExistingLoraWidgetBeforeRemoval && anExistingLoraWidgetBeforeRemoval.options && anExistingLoraWidgetBeforeRemoval.options.values) {
                    loraOptionsList = anExistingLoraWidgetBeforeRemoval.options.values;
                } else if (node.widgets_values && typeof node.widgets_values.lora_1_options !== "undefined") {
                    // A convention could be to save options in widgets_values if they are dynamic.
                     loraOptionsList = node.widgets_values.lora_1_options;
                }
                // If still no list, use a hardcoded default or ensure Python provides it.
                // For now, it might default to just ["none"] if no other source is found by this logic.


                for (let i = 1; i <= numLoras; i++) {
                    const loraWidgetName = `lora_${i}`;
                    const savedValue = node.properties[loraWidgetName];
                    const defaultValue = loraOptionsList.includes(savedValue) ? savedValue : loraOptionsList[0] || "none";

                    node.addWidget(
                        "combo",
                        loraWidgetName,
                        defaultValue,
                        (value) => { node.properties[loraWidgetName] = value; },
                        { values: loraOptionsList }
                    );
                }

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
                const new_computed_size = node.computeSize(); // Calculate the ideal size based on new content
                node.setSize(new_computed_size); // Set the node to this computed size
                
                node.setDirtyCanvas(true, true);
            };

            const numLorasWidget = node.widgets.find(w => w.name === "number_of_loras");
            if (numLorasWidget) {
                const originalCallback = numLorasWidget.callback;
                numLorasWidget.callback = (value) => {
                    numLorasWidget.value = parseInt(value, 10);
                    if (isNaN(numLorasWidget.value)) numLorasWidget.value = 1;
                    if (originalCallback) originalCallback.call(numLorasWidget, numLorasWidget.value);
                    updateDynamicWidgets();
                };
            }

            const onNodeConfigure = node.onConfigure;
            node.onConfigure = function(info) {
                if (onNodeConfigure) onNodeConfigure.apply(this, arguments);
                if (!this.properties) this.properties = {}; // Ensure properties exists

                if (info.widgets_values) {
                    for (let i = 1; i <= 20; i++) {
                        const loraWidgetName = `lora_${i}`;
                        if (info.widgets_values[loraWidgetName] !== undefined) {
                            this.properties[loraWidgetName] = info.widgets_values[loraWidgetName];
                        }
                    }
                     // If lora options were saved, restore them
                    if (typeof info.widgets_values.lora_1_options !== "undefined") {
                        this.widgets_values.lora_1_options = info.widgets_values.lora_1_options;
                    }
                }
                setTimeout(updateDynamicWidgets, 50);
            };
            
            // To ensure loraOptionsList is available when the node is first created or loaded
            // we might need to extract it from INPUT_TYPES definition if possible, or have Python save it.
            // One way: Python adds a hidden widget or property with the LoRA list.
            // For now, make a placeholder for how Python might provide this:
            if (!node.widgets_values) node.widgets_values = {};
            if (node.widgets && node.widgets.find(w=>w.name==="lora_1") && node.widgets.find(w=>w.name==="lora_1").options.values) {
                 node.widgets_values.lora_1_options = node.widgets.find(w=>w.name==="lora_1").options.values;
            } else {
                // Attempt to get it from the class's default widget definitions if available
                // This part is highly dependent on how ComfyUI stores original widget definitions accessible to JS
                // For now, if it's not found, loraOptionsList will default to ["none"] inside updateDynamicWidgets.
            }


            setTimeout(updateDynamicWidgets, 100);
        }
    }
});
