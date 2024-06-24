import tkinter as tk
from tkinter import scrolledtext, messagebox, ttk, filedialog
from xml.dom import minidom
import re
import asyncio
import threading

class XAMLFormatterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("XAML Formatter and Validator for WinUI3")
        self.root.geometry("800x700")

        self.setup_ui()
        self.setup_menu()

        self.undo_stack = []
        self.redo_stack = []

    def setup_ui(self):
        self.textbox = scrolledtext.ScrolledText(self.root, wrap=tk.WORD, font=("Courier New", 12))
        self.textbox.pack(padx=10, pady=10, expand=True, fill=tk.BOTH)
        self.textbox.bind("<KeyRelease>", self.on_text_change)
        self.textbox.bind("<Control-z>", self.undo)
        self.textbox.bind("<Control-y>", self.redo)

        self.output_textbox = scrolledtext.ScrolledText(self.root, wrap=tk.WORD, height=10, font=("Courier New", 10))
        self.output_textbox.pack(padx=10, pady=10, expand=True, fill=tk.BOTH)

        self.progress_bar = ttk.Progressbar(self.root, orient="horizontal", length=400, mode="determinate")
        self.progress_bar.pack(pady=10)

        self.format_button = tk.Button(self.root, text="Format and Validate", command=self.start_format_and_validate)
        self.format_button.pack(pady=10)

        self.setup_tags()

    def setup_menu(self):
        menubar = tk.Menu(self.root)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Open", command=self.open_file)
        file_menu.add_command(label="Save", command=self.save_file)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        menubar.add_cascade(label="File", menu=file_menu)
        self.root.config(menu=menubar)

    def setup_tags(self):
        self.textbox.tag_configure("tag_element", foreground="blue")
        self.textbox.tag_configure("tag_attribute", foreground="red")
        self.textbox.tag_configure("tag_value", foreground="green")
        self.textbox.tag_configure("tag_error", background="yellow", foreground="red")

    def on_text_change(self, event=None):
        content = self.textbox.get("1.0", tk.END)
        self.undo_stack.append(content)
        self.redo_stack.clear()
        self.apply_syntax_highlighting_async()

    def start_format_and_validate(self):
        threading.Thread(target=lambda: asyncio.run(self.format_and_validate_xaml())).start()

    async def format_and_validate_xaml(self):
        self.progress_bar["value"] = 0
        self.output_textbox.delete("1.0", tk.END)
        xaml_input = self.textbox.get("1.0", tk.END)

        try:
            self.update_progress("Parsing XAML...", 20)
            formatted_xaml, errors = await self.format_xaml_text(xaml_input)

            self.update_progress("Formatting XAML...", 40)
            self.textbox.delete("1.0", tk.END)
            self.textbox.insert(tk.INSERT, formatted_xaml)
            await self.apply_syntax_highlighting()

            self.update_progress("Validating XAML...", 60)
            if errors:
                self.output_textbox.insert(tk.INSERT, "Errors found in XAML:\n")
                for error in errors:
                    self.output_textbox.insert(tk.INSERT, f"- {error}\n")
                await self.highlight_errors(formatted_xaml, errors)
            else:
                self.output_textbox.insert(tk.INSERT, "Success: XAML formatted and validated successfully!\n")

            self.update_progress("Operation Complete", 100)
        except Exception as e:
            self.output_textbox.insert(tk.INSERT, f"An error occurred: {str(e)}\n")
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
            self.update_progress("Operation Failed", 100)

    def update_progress(self, message, value):
        self.output_textbox.insert(tk.INSERT, f"{message}\n")
        self.progress_bar["value"] = value
        self.root.update_idletasks()

    async def format_xaml_text(self, xaml):
        def format_task():
            errors = []
            try:
                parsed_xml = minidom.parseString(xaml)
                formatted_xml = self.pretty_print(parsed_xml)
                errors = self.validate_xaml(parsed_xml)
                return formatted_xml, errors
            except Exception as e:
                errors.append(f"Syntax error: {str(e)}")
                return xaml, errors

        return await asyncio.to_thread(format_task)

    def pretty_print(self, xml_node, indent="  "):
        def remove_whitespace_nodes(node, unlink=True):
            remove_list = []
            for child in node.childNodes:
                if child.nodeType == minidom.Node.TEXT_NODE and not child.data.strip():
                    remove_list.append(child)
                elif child.hasChildNodes():
                    remove_whitespace_nodes(child, unlink)
            for node in remove_list:
                node.parentNode.removeChild(node)
                if unlink:
                    node.unlink()

        remove_whitespace_nodes(xml_node)
        return self.format_node(xml_node, indent, 0)

    def format_node(self, node, indent, level):
        output = []
        if node.nodeType == minidom.Node.ELEMENT_NODE:
            output.append(f"{indent * level}<{node.tagName}")
            for attr_name, attr_value in node.attributes.items():
                output.append(f' {attr_name}="{attr_value}"')
            if node.childNodes:
                output.append(">\n")
                for child in node.childNodes:
                    output.append(self.format_node(child, indent, level + 1))
                output.append(f"{indent * level}</{node.tagName}>\n")
            else:
                output.append(" />\n")
        elif node.nodeType == minidom.Node.TEXT_NODE:
            text = node.data.strip()
            if text:
                output.append(f"{indent * level}{text}\n")
        return ''.join(output)

    def apply_syntax_highlighting_async(self):
        threading.Thread(target=lambda: asyncio.run(self.apply_syntax_highlighting())).start()

    async def apply_syntax_highlighting(self):
        content = self.textbox.get("1.0", tk.END)
        
        self.textbox.tag_remove("tag_element", "1.0", tk.END)
        self.textbox.tag_remove("tag_attribute", "1.0", tk.END)
        self.textbox.tag_remove("tag_value", "1.0", tk.END)
        
        def highlight_task():
            element_pattern = re.compile(r'<[^>]+>')
            attribute_pattern = re.compile(r'\b\w+="[^"]*"')
            value_pattern = re.compile(r'"[^"]*"')

            for pattern, tag in [
                (element_pattern, "tag_element"),
                (attribute_pattern, "tag_attribute"),
                (value_pattern, "tag_value")
            ]:
                for match in pattern.finditer(content):
                    start, end = match.span()
                    self.textbox.tag_add(tag, f"1.0+{start}c", f"1.0+{end}c")

        await asyncio.to_thread(highlight_task)

    def validate_xaml(self, xml_node):
        errors = []
        validation_functions = [
            self.check_for_missing_tags,
            self.check_for_unknown_elements,
            self.check_for_invalid_attributes,
            self.check_for_binding_errors,
            self.check_for_resource_errors,
            self.check_for_style_template_errors,
            self.check_for_namespace_errors,
            self.check_for_control_errors,
            self.check_for_event_handler_errors,
            self.check_for_template_binding_errors,
            self.check_for_visual_tree_errors,
            self.check_for_datatemplate_errors,
            self.check_for_converter_errors,
            self.check_for_style_conflicts,
            self.check_for_animation_storyboard_errors,
            self.check_for_markup_extension_errors,
            self.check_for_control_template_part_errors
        ]
        for func in validation_functions:
            errors.extend(func(xml_node))
        return errors

    def check_for_missing_tags(self, xml_node):
        errors = []
        for node in xml_node.getElementsByTagName("*"):
            if not node.hasChildNodes() and not node.hasAttributes():
                errors.append(f"Element <{node.tagName}> is empty and might be missing child elements or attributes.")
        return errors

    def check_for_unknown_elements(self, xml_node):
        errors = []
        known_elements = {
            'Page', 'ResourceDictionary', 'Grid', 'StackPanel', 'Canvas', 'TextBlock', 'Button',
            'TabView', 'TabViewItem', 'ComboBox', 'FontIcon', 'DataTemplate', 'ItemsControl',
            'Border', 'ToolTip', 'ToolTipService', 'Flyout', 'ProgressRing', 'controls:DataGrid',
            'controls:DataGridTextColumn', 'controls:DockPanel', 'SolidColorBrush'
        }  # Extend this list with more known elements as needed.
        for node in xml_node.getElementsByTagName("*"):
            if node.tagName not in known_elements:
                errors.append(f"Unknown element: <{node.tagName}>")
        return errors

    def check_for_invalid_attributes(self, xml_node):
        errors = []
        known_attributes = {
            'Grid': {'Row', 'Column', 'RowDefinitions', 'ColumnDefinitions', 'Background', 'Opacity', 'Visibility'},
            'TextBlock': {'Text', 'FontSize', 'Foreground', 'HorizontalAlignment', 'VerticalAlignment', 'Margin', 'Grid.Row', 'Grid.Column', 'Grid.ColumnSpan', 'Visibility', 'Style'},
            'Button': {'Content', 'Click', 'Command', 'Style', 'Margin', 'Padding', 'Height', 'Width', 'IsEnabled', 'ToolTipService.ToolTip', 'HorizontalAlignment', 'FontSize'},
            'ComboBox': {'ItemsSource', 'SelectedItem', 'IsEditable', 'Width', 'Height', 'ToolTipService.ToolTip', 'Margin', 'HorizontalAlignment', 'VerticalAlignment'},
            'TabView': {'TabItems', 'SelectedItem'},
            'DataTemplate': {'DataType'},
            'ItemsControl': {'ItemTemplate', 'ItemsSource'},
            'Border': {'Background', 'BorderBrush', 'BorderThickness', 'CornerRadius'},
            'ToolTip': {'Content', 'Placement'},
            'Flyout': {'Content', 'Placement'},
            'ProgressRing': {'IsActive', 'Width', 'Height'},
            'controls:DataGrid': {'ItemsSource', 'AutoGenerateColumns', 'Columns'},
            'controls:DataGridTextColumn': {'Header', 'Binding'},
            'controls:DockPanel': {'LastChildFill', 'Dock'},
            'SolidColorBrush': {'Color'}
        }  # Extend this list with more known attributes for elements as needed.
        for node in xml_node.getElementsByTagName("*"):
            if node.tagName in known_attributes:
                for attr_name in node.attributes.keys():
                    if attr_name not in known_attributes[node.tagName]:
                        errors.append(f"Unknown attribute {attr_name} in element <{node.tagName}>")
        return errors

    def check_for_binding_errors(self, xml_node):
        errors = []
        binding_pattern = re.compile(r"{Binding\s+Path=([^,}]+),?\s*}")
        for node in xml_node.getElementsByTagName("*"):
            for attr_name, attr_value in node.attributes.items():
                binding_match = binding_pattern.search(attr_value)
                if binding_match:
                    path = binding_match.group(1)
                    if not path:  # Simplified check, more detailed checks can be implemented.
                        errors.append(f"Binding path error in attribute {attr_name} of element <{node.tagName}>")
        return errors

    def check_for_resource_errors(self, xml_node):
        errors = []
        resources = set()
        for node in xml_node.getElementsByTagName("*"):
            if node.tagName == "ResourceDictionary" or "Resource" in node.tagName:
                for child in node.childNodes:
                    if child.nodeType == minidom.Node.ELEMENT_NODE and 'x:Key' in child.attributes:
                        resources.add(child.attributes['x:Key'].value)
        for node in xml_node.getElementsByTagName("*"):
            for attr_name, attr_value in node.attributes.items():
                if "StaticResource" in attr_value or "DynamicResource" in attr_value:
                    resource_key = re.search(r'\{(Static|Dynamic)Resource\s+(\w+)\}', attr_value)
                    if resource_key and resource_key.group(2) not in resources:
                        errors.append(f"Resource '{resource_key.group(2)}' not found in element <{node.tagName}>")
        return errors

    def check_for_style_template_errors(self, xml_node):
        errors = []
        for node in xml_node.getElementsByTagName("*"):
            if "Style" in node.tagName or "Template" in node.tagName:
                if 'TargetType' not in node.attributes:
                    errors.append(f"Style or Template in element <{node.tagName}> missing 'TargetType' attribute")
                if node.tagName == "Style" and 'BasedOn' in node.attributes:
                    based_on = node.attributes['BasedOn'].value
                    if not re.match(r'\{StaticResource \w+\}', based_on):
                        errors.append(f"Invalid BasedOn reference '{based_on}' in <{node.tagName}>")
        return errors

    def check_for_namespace_errors(self, xml_node):
        errors = []
        namespaces = {node.prefix for node in xml_node.childNodes if node.nodeType == minidom.Node.ELEMENT_NODE}
        for node in xml_node.getElementsByTagName("*"):
            for attr_name, attr_value in node.attributes.items():
                if ':' in attr_name:
                    prefix = attr_name.split(':')[0]
                    if prefix not in namespaces:
                        errors.append(f"Namespace prefix '{prefix}' not defined for attribute {attr_name} in element <{node.tagName}>")
        return errors

    def check_for_control_errors(self, xml_node):
        errors = []
        known_controls = {
            'Button', 'TextBox', 'TextBlock', 'Page', 'Grid', 'StackPanel', 'Canvas', 'ComboBox',
            'TabView', 'TabViewItem', 'FontIcon', 'DataTemplate', 'ItemsControl', 'Border', 'ToolTip',
            'ToolTipService', 'Flyout', 'ProgressRing', 'controls:DataGrid', 'controls:DataGridTextColumn',
            'controls:DockPanel', 'SolidColorBrush', 'local:HalfWidthConverter', 'local:BooleanToVisibilityConverter',
            'local:InvertBooleanConverter', 'local:NullableBooleanToBooleanConverter', 'local:TemplateSelector'
        }  # Extend this list with more known controls as needed.
        for node in xml_node.getElementsByTagName("*"):
            if node.tagName not in known_controls:
                errors.append(f"Unknown control: <{node.tagName}>")
        return errors

    def check_for_event_handler_errors(self, xml_node):
        errors = []
        event_pattern = re.compile(r'^[A-Za-z_]\w*$')
        for node in xml_node.getElementsByTagName("*"):
            for attr_name in node.attributes.keys():
                if 'Click' in attr_name or 'Handler' in attr_name:
                    handler_name = node.attributes[attr_name].value
                    if not event_pattern.match(handler_name):
                        errors.append(f"Invalid event handler name '{handler_name}' in attribute {attr_name} of element <{node.tagName}>")
        return errors

    def check_for_template_binding_errors(self, xml_node):
        errors = []
        for node in xml_node.getElementsByTagName("*"):
            for attr_name, attr_value in node.attributes.items():
                if "TemplateBinding" in attr_value:
                    template_binding = re.search(r'\{TemplateBinding\s+(\w+)\}', attr_value)
                    if template_binding and template_binding.group(1) not in node.attributes:
                        errors.append(f"Invalid TemplateBinding '{template_binding.group(1)}' in element <{node.tagName}>")
        return errors

    def check_for_visual_tree_errors(self, xml_node):
        errors = []
        for node in xml_node.getElementsByTagName("*"):
            if node.tagName == "VisualTree" and not node.hasChildNodes():
                errors.append(f"VisualTree element <{node.tagName}> is empty")
        return errors

    def check_for_datatemplate_errors(self, xml_node):
        errors = []
        for node in xml_node.getElementsByTagName("DataTemplate"):
            if not node.hasChildNodes():
                errors.append(f"DataTemplate element <{node.tagName}> is empty")
        return errors

    def check_for_converter_errors(self, xml_node):
        errors = []
        for node in xml_node.getElementsByTagName("*"):
            for attr_name, attr_value in node.attributes.items():
                if "Converter" in attr_name:
                    converter = re.search(r'\{(\w+Converter)\}', attr_value)
                    if converter and converter.group(1) not in globals():
                        errors.append(f"Converter '{converter.group(1)}' not found in element <{node.tagName}>")
        return errors

    def check_for_style_conflicts(self, xml_node):
        errors = []
        for node in xml_node.getElementsByTagName("Style"):
            if 'TargetType' in node.attributes:
                target_type = node.attributes['TargetType'].value
                if any(child.tagName == "Style" and child != node and 'TargetType' in child.attributes and child.attributes['TargetType'].value == target_type for child in xml_node.getElementsByTagName("Style")):
                    errors.append(f"Conflicting styles for TargetType '{target_type}' in element <{node.tagName}>")
        return errors

    def check_for_animation_storyboard_errors(self, xml_node):
        errors = []
        for node in xml_node.getElementsByTagName("Storyboard"):
            for child in node.childNodes:
                if child.nodeType == minidom.Node.ELEMENT_NODE and 'TargetProperty' not in child.attributes:
                    errors.append(f"Animation <{child.tagName}> in Storyboard missing 'TargetProperty' attribute")
        return errors

    def check_for_markup_extension_errors(self, xml_node):
        errors = []
        for node in xml_node.getElementsByTagName("*"):
            for attr_name, attr_value in node.attributes.items():
                if "MarkupExtension" in attr_value:
                    markup_extension = re.search(r'\{(\w+Extension)\}', attr_value)
                    if markup_extension and markup_extension.group(1) not in globals():
                        errors.append(f"MarkupExtension '{markup_extension.group(1)}' not found in element <{node.tagName}>")
        return errors

    def check_for_control_template_part_errors(self, xml_node):
        errors = []
        for node in xml_node.getElementsByTagName("*"):
            if "ControlTemplate" in node.tagName:
                for child in node.childNodes:
                    if child.nodeType == minidom.Node.ELEMENT_NODE and 'x:Name' not in child.attributes:
                        errors.append(f"ControlTemplate part <{child.tagName}> missing 'x:Name' attribute in element <{node.tagName}>")
        return errors

    async def highlight_errors(self, content, errors):
        def highlight_task():
            for error in errors:
                match = re.search(re.escape(error), content)
                if match:
                    start, end = match.span()
                    self.textbox.tag_add("tag_error", f"1.0+{start}c", f"1.0+{end}c")

        await asyncio.to_thread(highlight_task)

    def undo(self, event=None):
        if len(self.undo_stack) > 1:
            current_content = self.undo_stack.pop()
            self.redo_stack.append(current_content)
            previous_content = self.undo_stack[-1]
            self.textbox.delete("1.0", tk.END)
            self.textbox.insert(tk.INSERT, previous_content)
            self.apply_syntax_highlighting_async()

    def redo(self, event=None):
        if self.redo_stack:
            next_content = self.redo_stack.pop()
            self.undo_stack.append(next_content)
            self.textbox.delete("1.0", tk.END)
            self.textbox.insert(tk.INSERT, next_content)
            self.apply_syntax_highlighting_async()

    def open_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("XAML files", "*.xaml"), ("All files", "*.*")])
        if file_path:
            threading.Thread(target=self.load_file, args=(file_path,)).start()

    def load_file(self, file_path):
        with open(file_path, 'r') as file:
            content = file.read()
            self.root.after(0, self.update_textbox, content)

    def update_textbox(self, content):
        self.textbox.delete("1.0", tk.END)
        self.textbox.insert(tk.INSERT, content)
        self.apply_syntax_highlighting_async()

    def save_file(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".xaml", filetypes=[("XAML files", "*.xaml"), ("All files", "*.*")])
        if file_path:
            threading.Thread(target=self.save_file_task, args=(file_path,)).start()

    def save_file_task(self, file_path):
        content = self.textbox.get("1.0", tk.END)
        with open(file_path, 'w') as file:
            file.write(content)

if __name__ == "__main__":
    root = tk.Tk()
    app = XAMLFormatterApp(root)
    root.mainloop()
