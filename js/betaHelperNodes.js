import { app } from "/scripts/app.js";

app.registerExtension({
    name: "Comfy.BETAHelperNodes.IndexedLoraLoader",
    async nodeCreated(node) {
        if (node.type === "IndexedLoRALoader_BETA") { // Make sure this matches your NODE_CLASS_MAPPINGS key
            const numberWidget = node.widgets.find(w => w.name === "number_of_loras");
            const indexWidget = node.widgets.find(w => w.name === "index"); // Get the index widget

            if (!numberWidget) {
                console.error("Could not find number_of_loras widget for IndexedLoRALoader_BETA");
                return;
            }

            const updateLoraWidgetsVisibility = () => {
                const numLoras = numberWidget.value;

                // Update visibility of lora_X widgets
                for (let i = 1; i <= 20; i++) { // Assuming max 20 lora slots as per your Python
                    const loraWidget = node.widgets.find(w => w.name === `lora_${i}`);
                    if (loraWidget) {
                        loraWidget.inputEl.style.display = (i <= numLoras) ? "" : "none";
                        // For some widget types, you might need to hide the parent or a different element
                        // If the above doesn't work, try:
                        // loraWidget.inputEl.parentElement.parentElement.style.display = (i <= numLoras) ? "" : "none";
                        // or inspect the DOM to find the correct element to hide.
                    }
                }

                // Update the max value of the index widget
                if (indexWidget) {
                    indexWidget.options.max = numLoras;
                    // If the current index value is greater than the new max, clamp it
                    if (indexWidget.value > numLoras) {
                        indexWidget.value = numLoras;
                    }
                    // Force redraw/update of the widget if necessary (might not be needed for simple max change)
                    if (indexWidget.inputEl.max !== undefined) {
                         indexWidget.inputEl.max = numLoras;
                    }
                }
            };

            // Initial call to set visibility based on default value
            updateLoraWidgetsVisibility();

            // Add listener for changes to number_of_loras
            numberWidget.callback = (value) => {
                numberWidget.value = parseInt(value, 10); // Ensure it's an integer
                updateLoraWidgetsVisibility();
                // If you have app.graph.setDirtyCanvas, you might call it here if UI doesn't fully refresh
                // app.graph.setDirtyCanvas(true, true);
            };

            // Optional: If you want the index widget to also trigger a graph re-run on change (like other inputs)
            // indexWidget.callback = (value) => {
            //    indexWidget.value = parseInt(value, 10);
            //    // app.graph.setDirtyCanvas(true, true); // If needed
            // };
        }
    }
});
