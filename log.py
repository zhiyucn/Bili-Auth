import os

class Log:
    def __init__(self,filename):
        self.filename = filename
        if not os.path.exists(filename):
            with open(filename, 'w') as f:
                f.write('[INFO]LOG SYSYTEM STARTED'+ os.linesep)
        
    def log(self, message, level='INFO'):
        print(f'[{level}] {message}')
        with open(self.filename, 'a+') as f:
            f.write('['+level+'] '+message+os.linesep)
    def delete_log(self):
        os.remove(self.filename)
    def output_log(self):
        with open(self.filename, 'r') as f:
            return f.read()