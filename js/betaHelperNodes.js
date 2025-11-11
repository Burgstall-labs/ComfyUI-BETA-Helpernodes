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
            
            // Store the original/master list of all outputs if not already stored
            // This serves as our template to rebuild from
            if (!node.all_outputs || node.all_outputs.length === 0) {
                // Clone the outputs array to preserve the master list
                node.all_outputs = node.outputs ? [...node.outputs] : [];
                console.log(`[BETA Helper Nodes] Stored master outputs list: ${node.all_outputs.length} outputs`);
            }
            
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
                
                // Ensure we have the master list
                if (!node.all_outputs || node.all_outputs.length !== totalExpectedOutputs) {
                    console.warn(`[BETA Helper Nodes] Master outputs list invalid. Expected ${totalExpectedOutputs}, got ${node.all_outputs?.length || 0}`);
                    // Try to rebuild master list from current outputs if available
                    if (node.outputs && node.outputs.length === totalExpectedOutputs) {
                        node.all_outputs = [...node.outputs];
                        console.log(`[BETA Helper Nodes] Rebuilt master outputs list from current outputs`);
                    } else {
                        return; // Can't proceed without master list
                    }
                }
                
                // Rebuild the outputs array:
                // 1. Take the first 'clampedMaxScenes' scene outputs from master list
                // 2. Append the 3 standard outputs (scene_frames, scene_summary, scene_count) from the end of master list
                const newOutputs = [];
                
                // Add visible scene outputs (scene_1 through scene_max_scenes)
                for (let i = 0; i < clampedMaxScenes; i++) {
                    if (node.all_outputs[i]) {
                        newOutputs.push(node.all_outputs[i]);
                    }
                }
                
                // Add the 3 standard outputs from the end (scene_frames, scene_summary, scene_count)
                for (let i = MAX_SCENES; i < totalExpectedOutputs; i++) {
                    if (node.all_outputs[i]) {
                        newOutputs.push(node.all_outputs[i]);
                    }
                }
                
                // Replace the node's outputs array with the rebuilt one
                // Clear existing outputs first to ensure clean state
                if (node.outputs && node.outputs.length > 0) {
                    // Disconnect any existing connections to outputs we're removing
                    for (let i = clampedMaxScenes; i < MAX_SCENES; i++) {
                        if (node.outputs[i] && node.outputs[i].links) {
                            // Links are managed by ComfyUI, but we can try to clean up
                            const links = node.outputs[i].links || [];
                            for (const linkId of links) {
                                const link = app.graph.links[linkId];
                                if (link) {
                                    // ComfyUI will handle link cleanup, but we ensure outputs are updated
                                }
                            }
                        }
                    }
                }
                
                // Replace outputs array
                node.outputs = newOutputs;
                
                console.log(`[BETA Helper Nodes] Updated Scene Detection outputs: ${clampedMaxScenes} scene outputs + 3 standard outputs = ${newOutputs.length} total`);
                
                // Also manipulate DOM directly as a fallback to ensure visual update
                // ComfyUI nodes typically have outputs in a specific DOM structure
                try {
                    const nodeElement = node.el || node.domElement || (node.constructor && node.constructor.prototype && node.constructor.prototype.el);
                    if (nodeElement) {
                        // Find all output elements - ComfyUI typically uses classes like 'output' or structure in .outputs container
                        const outputContainer = nodeElement.querySelector('.outputs') || nodeElement;
                        const allOutputElements = outputContainer.querySelectorAll('.output, [class*="output"]');
                        
                        // Hide outputs beyond max_scenes (but keep the last 3 visible)
                        allOutputElements.forEach((el, index) => {
                            if (index < MAX_SCENES) {
                                // Scene outputs: hide if beyond clampedMaxScenes
                                el.style.display = index < clampedMaxScenes ? "" : "none";
                            } else if (index >= MAX_SCENES && index < totalExpectedOutputs) {
                                // Standard outputs: always show
                                el.style.display = "";
                            }
                        });
                    }
                } catch (e) {
                    console.warn(`[BETA Helper Nodes] Could not update DOM directly: ${e.message}`);
                }
                
                // Force node to recalculate size and redraw
                // Use ComfyUI's methods to ensure proper update
                if (node.onResize) {
                    node.onResize();
                }
                const new_computed_size = node.computeSize();
                node.setSize(new_computed_size);
                node.setDirtyCanvas(true, true);
                
                // Trigger ComfyUI's output update if method exists
                if (node.onOutputsChanged) {
                    node.onOutputsChanged();
                }
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
                // Ensure master list is preserved during configuration
                if (!this.all_outputs || this.all_outputs.length === 0) {
                    if (this.outputs && this.outputs.length > 0) {
                        // If we lost the master list, try to restore it
                        // This might happen if the node was saved/loaded
                        const totalExpected = MAX_SCENES + 3;
                        if (this.outputs.length === totalExpected) {
                            this.all_outputs = [...this.outputs];
                        }
                    }
                }
                setTimeout(updateDynamicOutputs, 50);
            };
            
            // Initial update after a short delay to ensure node is fully initialized
            setTimeout(updateDynamicOutputs, 100);
        }
    }
});