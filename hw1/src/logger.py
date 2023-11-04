import datetime


class Logger:
    def __init__(self, file):
        self.file = file
        self.error_mode = True
        self.info_mode = True
        self.warning_mode = True
        self.status = True
        self.print_mode = True

    def err(self, add_fields, text):
        if not self.error_mode:
            return
        self.create_row("ERROR", add_fields, text)

    def info(self, add_fields, text):
        if not self.info:
            return
        self.create_row("INFO", add_fields, text)

    def warning(self, add_fields, text):
        if not self.warning_mode:
            return
        self.create_row("WARNING", add_fields, text)

    def create_row(self, type_msg, add_fields, text):
        if not self.status:
            return

        add = ['[' + str(field) + ']' for field in add_fields]
        row = f"[{type_msg}][{datetime.datetime.now()}]{''.join(add)} {text}\n"

        with open(self.file, 'w+') as log:
            log.write(row)

        if self.print_mode:
            print(row)
