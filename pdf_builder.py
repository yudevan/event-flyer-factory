from reportlab.lib.units import inch
from os.path import isfile, join, basename, splitext
from wand.image import Image
from wand.color import Color
from os import listdir
import tempfile, PyPDF2

import layouts

dummy_event = {
        "name": "Placeholder Event for Flyer Factory",
        "start_dt": "2015-09-08 12:00:00",
        "timezone": "PDT",
        "description": "Fremont for Bernie Sanders is hosting Mario Brown of the&nbsp;Washington State Democratic Chairs Organization to learn more about caucusing for Bernie Sanders in 2016.&nbsp; Mario will explain how the caucus works in Washington and how we can get involved to get Senator Sanders elected in November!  ...",
        "venue_addr1": "1234 Somestreet NW",
        "venue_city": "Seattle",
        "venue_name": "A venue somewhere",
        "venue_zip": "98109"
        }


def build_pdf(template_name, layout_name, events, fname):
    with open(join("flyer-templates", template_name + ".pdf"), "rb") as template_file:
        template = PyPDF2.PdfFileReader(template_file)
        template_page = template.getPage(0)
        box = template_page.mediaBox
        pagesize = (float(box[2] - box[0]), float(box[3] - box[1]))
        layout = layouts.layouts()[layout_name]()
        with tempfile.NamedTemporaryFile() as event_pdf:
            layout.fill(event_pdf, pagesize, events, pagesize[1]/3, 0.5*inch, 0.5*inch)
            event_page = PyPDF2.PdfFileReader(event_pdf).getPage(0)
            template_page.mergePage(event_page)
            with open(fname, "wb") as out:
                merged = PyPDF2.PdfFileWriter()
                merged.addPage(template_page)
                merged.write(out)


def get_preview(template_name, layout_name):
    preview_name = join("previews", template_name + "_" + layout_name + ".jpg")
    if isfile(preview_name):
        return preview_name
    else:
        with tempfile.NamedTemporaryFile() as tmp_pdf:
            build_pdf(template_name, layout_name, [dummy_event] * 40, tmp_pdf.name)
            with Image(filename=tmp_pdf.name, resolution=100) as pdf:
                pdf.resize(300, int(round(300 / pdf.width * pdf.height)))
                pdf.background_color = Color("white")
                pdf.alpha_channel = "remove"
                pdf.save(filename=preview_name)
        return preview_name


