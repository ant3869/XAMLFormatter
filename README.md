# XAMLFormatter

"""
XAML Formatter and Validator for WinUI3

This application is designed to format and validate XAML code used in WinUI3 applications.
It provides real-time syntax highlighting, detailed error checking, and progress tracking
for formatting and validation operations.

Features:
1. Real-time Syntax Highlighting:
   - The application updates the text color dynamically as the user types in the main text box.
   - Elements, attributes, values, and errors are highlighted in different colors for better readability.

2. Formatting and Validation:
   - The "Format and Validate" button triggers the formatting and validation process.
   - The application parses the XAML input, formats it neatly, and validates it against common XAML errors.
   - Errors are highlighted in the text box and detailed error messages are displayed in the output text box.

3. Logging and Output:
   - A second text box is provided below the main text box for logging and output messages.
   - The output text box displays messages about the progress and results of the formatting and validation operations.

4. Progress Bar:
   - A progress bar is included to show the progress of the formatting and validation operations.
   - The progress bar updates from 0 to 100, reflecting the current operation's progress.

Error Checking:
- The application checks for various types of XAML errors, including:
  - Missing or mismatched tags
  - Unknown elements or attributes
  - Invalid attribute values
  - Binding errors
  - Resource errors
  - Style and template errors
  - Namespace errors
  - Control errors
  - Event handler errors
  - Template binding errors
  - Visual tree errors
  - DataTemplate errors
  - Converter errors
  - Style conflicts
  - Animation and storyboard errors
  - Markup extension errors
  - Control template part errors

Usage:
- Run the application and enter your XAML code into the main text box.
- The syntax highlighting will update as you type.
- Click the "Format and Validate" button to format the XAML and check for errors.
- The progress bar will indicate the progress of the operation.
- Check the output text box for detailed error messages and logs.

Dependencies:
- tkinter: For creating the GUI components.
- xml.dom.minidom: For parsing and formatting the XAML.

This application provides a user-friendly interface for working with XAML code in WinUI3,
making it easier to identify and fix errors while maintaining a neat and readable format.
"""
