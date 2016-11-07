from openerp import fields, models, exceptions, api, _
from datetime import date
from datetime import datetime
import base64
import csv
import cStringIO


class rapport_correctifs(models.TransientModel):
    _name = 'cmim.rapport.correctif'
    _description = """Assistant de generation du rapport des correctifs"""

    data = fields.Binary('File', required=True)
    name = fields.Char('Filename')
    delimeter = fields.Char('Delimeter', default=',',
                            help='Default delimeter is ","')
 
    date_debut = fields.Date(string="date de debut", required=True)
    date_fin = fields.Date(string="date de fin", required=True)

    def action_import(self):
        """Load Inventory data from the CSV file."""
        ctx = self._context
       
        data = base64.b64decode(self.data)
        file_input = cStringIO.StringIO(data)
        file_input.seek(0)
        reader_info = []
        if self.delimeter:
            delimeter = str(self.delimeter)
        else:
            delimeter = ','
        reader = csv.reader(file_input, delimiter=delimeter,
                            lineterminator='\r\n')
        try:
            reader_info.extend(reader)
        except Exception:
            raise exceptions.Warning(_("Not a valid file!"))
        keys = reader_info[0]
        
       
    