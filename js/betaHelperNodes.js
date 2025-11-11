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

                // CRITICAL: Save ALL current widget values BEFORE clearing widgets
                // This ensures we capture the most up-to-date values directly from widgets,
                // even if widget callbacks haven't fired yet or properties are stale
                for (let i = 1; i <= 20; i++) {
                    const loraWidget = node.widgets.find(w => w.name === `lora_${i}`);
                    if (loraWidget) {
                        // Always read the current widget value directly, don't rely on stale properties
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

// Scene Detection Node - Dynamic Output Sockets
app.registerExtension({
    name: "Comfy.BETAHelperNodes.SceneDetectLogic",
    async nodeCreated(node) {
        const expectedNodeTitle = "Scene Detect 🎥 🅑🅔🅣🅐"; // Match the node's display name

        if (node.title === expectedNodeTitle) {
            console.log(`[BETA Helper Nodes] MATCHED Scene Detection node: '${node.title}'`);

            const MAX_SCENES = 50; // Match Python MAX_SCENES constant
            
            const updateDynamicOutputs = () => {
                const maxScenesWidget = node.widgets.find(w => w.name === "max_scenes");
                if (!maxScenesWidget) {
                    console.error("[BETA Helper Nodes] 'max_scenes' widget not found!");
                    return;
                }
                
                const maxScenes = parseInt(maxScenesWidget.value, 10) || 10;
                const clampedMaxScenes = Math.max(1, Math.min(maxScenes, MAX_SCENES));
                
                // Expected total outputs: MAX_SCENES scene outputs + 3 standard outputs
                const totalExpectedOutputs = MAX_SCENES + 3;
                
                // Ensure node has outputs
                if (!node.outputs || node.outputs.length !== totalExpectedOutputs) {
                    console.warn(`[BETA Helper Nodes] Scene Detection node has ${node.outputs?.length || 0} outputs, expected ${totalExpectedOutputs}`);
                    return;
                }
                
                // Try multiple approaches to hide/show outputs
                // Approach 1: Use hidden property if it exists
                let usedHiddenProperty = false;
                for (let i = 0; i < MAX_SCENES; i++) {
                    if (node.outputs[i]) {
                        if ('hidden' in node.outputs[i]) {
                            node.outputs[i].hidden = i >= clampedMaxScenes;
                            usedHiddenProperty = true;
                        }
                    }
                }
                
                // Approach 2: Direct DOM manipulation (more reliable)
                try {
                    // Find the node's DOM element
                    const nodeEl = node.el || node.domElement;
                    if (nodeEl) {
                        // ComfyUI outputs are typically in a container with class 'outputs' or similar
                        // Each output has a specific structure - try to find them
                        const outputContainer = nodeEl.querySelector('.outputs') || nodeEl.querySelector('.node_outputs') || nodeEl;
                        
                        // Find all output socket elements - they typically have a specific class or structure
                        // Try multiple selectors to find output elements
                        let outputElements = outputContainer.querySelectorAll('.output, .node_output, [class*="output"]');
                        
                        // If that doesn't work, try finding by data attributes or structure
                        if (outputElements.length === 0) {
                            // Outputs might be direct children or in a specific structure
                            outputElements = outputContainer.querySelectorAll('div[class*="output"], .socket-output');
                        }
                        
                        // Hide/show outputs based on index
                        outputElements.forEach((el, index) => {
                            if (index < MAX_SCENES) {
                                // Scene outputs: hide if beyond clampedMaxScenes
                                if (index >= clampedMaxScenes) {
                                    el.style.display = 'none';
                                    el.style.visibility = 'hidden';
                                    el.style.height = '0';
                                    el.style.margin = '0';
                                    el.style.padding = '0';
                                } else {
                                    el.style.display = '';
                                    el.style.visibility = '';
                                    el.style.height = '';
                                    el.style.margin = '';
                                    el.style.padding = '';
                                }
                            } else if (index >= MAX_SCENES && index < totalExpectedOutputs) {
                                // Standard outputs: always show
                                el.style.display = '';
                                el.style.visibility = '';
                                el.style.height = '';
                                el.style.margin = '';
                                el.style.padding = '';
                            }
                        });
                        
                        console.log(`[BETA Helper Nodes] Found ${outputElements.length} output elements in DOM`);
                    }
                } catch (e) {
                    console.warn(`[BETA Helper Nodes] DOM manipulation failed: ${e.message}`);
                }
                
                console.log(`[BETA Helper Nodes] Updated Scene Detection outputs: ${clampedMaxScenes} scene outputs visible, ${MAX_SCENES - clampedMaxScenes} hidden (used hidden property: ${usedHiddenProperty})`);
                
                // Force node update - this is critical for ComfyUI to refresh the display
                if (typeof node.update === 'function') {
                    node.update();
                }
                if (typeof node.onResize === 'function') {
                    node.onResize();
                }
                
                // Recalculate size and redraw
                const new_computed_size = node.computeSize();
                node.setSize(new_computed_size);
                node.setDirtyCanvas(true, true);
            };
            
            // Watch for max_scenes widget changes
            const maxScenesWidget = node.widgets.find(w => w.name === "max_scenes");
            if (maxScenesWidget) {
                const originalCallback = maxScenesWidget.callback;
                maxScenesWidget.callback = (value) => {
                    maxScenesWidget.value = parseInt(value, 10) || 10;
                    if (isNaN(maxScenesWidget.value)) maxScenesWidget.value = 10;
                    maxScenesWidget.value = Math.max(1, Math.min(maxScenesWidget.value, MAX_SCENES));
                    if (originalCallback) originalCallback.call(maxScenesWidget, maxScenesWidget.value);
                    updateDynamicOutputs();
                };
            }
            
            // Handle node configuration/state restoration
            const onNodeConfigure = node.onConfigure;
            node.onConfigure = function(info) {
                if (onNodeConfigure) onNodeConfigure.apply(this, arguments);
                setTimeout(updateDynamicOutputs, 50);
            };
            
            // Initial update after a short delay to ensure node is fully initialized
            setTimeout(updateDynamicOutputs, 100);
        }
    }
});