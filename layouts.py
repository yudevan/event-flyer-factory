from reportlab.platypus import Flowable, Spacer, BaseDocTemplate, Table, TableStyle, FrameBreak
from reportlab.platypus.frames import Frame
from reportlab.platypus.flowables import KeepTogether
from reportlab.platypus.paragraph import Paragraph
from reportlab.platypus.doctemplate import PageTemplate
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.lib.units import inch

from PyPDF2 import PdfFileWriter, PdfFileReader

from itertools import chain, repeat
import arrow, re, os, sys, tempfile

if sys.version_info[0] < 3:
    import HTMLParser
    html = HTMLParser.HTMLParser()
else:
    import html

# register fonts for PDFs
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
pdfmetrics.registerFont(TTFont("FontAwesome", "fonts/fontawesome-webfont.ttf"))
pdfmetrics.registerFont(TTFont("Lato", "fonts/Lato2OFL/Lato-Regular.ttf"))
pdfmetrics.registerFont(TTFont("Lato Bold", "fonts/Lato2OFL/Lato-Bold.ttf"))
pdfmetrics.registerFont(TTFont("Lato Italic", "fonts/Lato2OFL/Lato-Italic.ttf"))

styles = {
        "default": ParagraphStyle("default", fontName="Lato", fontSize=10, allowWidows=1, splitLongWords=1),
        "small": ParagraphStyle("small", fontName="Lato", fontSize=8, allowWidows=1, splitLongWords=1,
            leading=8),
        "space-after": ParagraphStyle("default", fontName="Lato", fontSize=10, allowWidows=1, splitLongWords=1,
            spaceAfter=0.15*inch),
        "event-title": ParagraphStyle("event-title", fontName="Lato Bold", fontSize=10,
            allowWidows=1, splitLongWords=1),
        "event-time": ParagraphStyle("event-time", fontName="Lato Italic", fontSize=8,
            allowWidows=1, splitLongWords=1, leading=8),
        "event-description": ParagraphStyle("event-description", fontName="Lato Italic", fontSize=7,
            allowWidows=1, splitLongWords=1, spaceAfter=0.2*inch, leading=7),
        "xl-event-title": ParagraphStyle("xl-event-title", fontName="Lato Bold", fontSize=12,
            allowWidows=1, splitLongWords=1, alignment=TA_CENTER, spaceAfter=0.10*inch),
        "xl-event-venue": ParagraphStyle("xl-event-venue", fontName="Lato Bold", fontSize=8,
            allowWidows=1, splitLongWords=1, alignment=TA_CENTER),
        "xl-event-venue-address": ParagraphStyle("xl-event-venue-address", fontName="Lato", fontSize=7,
            allowWidows=1, splitLongWords=1, alignment=TA_CENTER),
        "xl-event-description": ParagraphStyle("xl-event-description", fontName="Lato", fontSize=9,
            allowWidows=1, splitLongWords=1, alignment=TA_CENTER),
        "pb-event-title": ParagraphStyle("xl-event-title", fontName="Lato Bold", fontSize=18,
            allowWidows=1, splitLongWords=1, alignment=TA_CENTER, spaceAfter=0.20*inch),
        "pb-event-venue": ParagraphStyle("xl-event-venue", fontName="Lato Bold", fontSize=12,
            allowWidows=1, splitLongWords=1, alignment=TA_CENTER),
        "pb-event-venue-address": ParagraphStyle("xl-event-venue-address", fontName="Lato", fontSize=12,
            allowWidows=1, splitLongWords=1, alignment=TA_CENTER, spaceAfter=0.10*inch),
        "pb-event-description": ParagraphStyle("xl-event-description", fontName="Lato", fontSize=10,
            allowWidows=1, splitLongWords=1, alignment=TA_CENTER),
        "xs-event-title": ParagraphStyle("xs-event-title", fontName="Lato Bold", fontSize=6,
            allowWidows=1, splitLongWords=1, spaceAfter=0, leading=6),
        "xs-event": ParagraphStyle("xs-event", fontName="Lato", fontSize=6, leading=6,
            allowWidows=1, splitLongWords=1),
        }

# A normal-sized event that fits into a 2-column layout.
class Event(object):
    def __init__(self, event):
        self.event = event
        self.name = event["name"]
        self.time = "%s %s" % (arrow.get(event["start_dt"], "YYYY-MM-DD HH:mm:ss").format("MM/D/YYYY, h:mma"),
                event["timezone"])
        self.description = html.unescape(event["description"])

        if "venue_addr1" in event and "venue_city" in event:
            addr = event["venue_addr1"].strip()
            city = event["venue_city"].strip()
            if len(addr) > 0 and len(city) > 0:
                self.place = "%s, %s" % (addr, city)
            else:
                self.place = ""
        else:
            self.place = ""

        self.venue_name = self.event["venue_name"]

        try:
            self.first_sentence = re.match(r'(?:[^.:;]+[.:;]){1}', self.description).group()
        except AttributeError:
            self.first_sentence = ""

    def render(self):
        return KeepTogether([
            Paragraph(self.name, styles["event-title"]),
            Spacer(height=3, width=0),
            Paragraph(self.time, styles["event-time"]),
            Paragraph(self.venue_name, styles["small"]),
            Paragraph(self.place, styles["small"]),
            Spacer(height=3, width=0),
            Paragraph(self.first_sentence, styles["event-description"]),
            ])

# A tiny event
class XSEvent(Event):
    table_style = TableStyle([("FONT", (0, 0), (0, -1), "FontAwesome"),
                              ("ALIGNMENT", (0, 0), (0, -1), "CENTER"),
                              ("VALIGN", (0, 0), (-1, -1), "TOP"),
                              ("SIZE", (0, 0), (-1, -1), 6),
                              ("LEFTPADDING", (0, 0), (-1, -1), 3),
                              ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                              ("BOTTOMPADDING", (0, 0), (-1, 0), 0),
                              ("BOTTOMPADDING", (0, 1), (-1, 1), 0),
                              ("LEADING", (0, 0), (-1, -1), 6),
                              ])

    def __init__(self, event):
        Event.__init__(self, event)

    def render(self):
        venue = [["\uf017", Paragraph(self.time, styles["xs-event"])],
                 ["\uf041", Paragraph(self.venue_name, styles["xs-event"])],
                 ["", Paragraph(self.place, styles["xs-event"])]]
        table = Table(venue, style=self.table_style, spaceAfter=8, colWidths=[8, None])
        table.hAlign = "LEFT"
        table.vAlign = "TOP"
        return KeepTogether([
            Paragraph(self.name, styles["xs-event-title"]),
            table,
            ])

# An extra-large event
class XLEvent(Event):
    def __init__(self, event):
        Event.__init__(self, event)

    def render(self):
        e = []
        e.append(Paragraph(self.name, styles["xl-event-title"]))
        e.append(Paragraph("%s, <b>%s</b>" % (self.time, self.venue_name), styles["xl-event-venue"]))
        if len(self.place) > 0:
            e.append(Paragraph(self.place, styles["xl-event-venue-address"]))
        e.append(Paragraph(self.description, styles["xl-event-description"]))
        return KeepTogether(e)

# Phonebank RSVP sheet top event
class PBEvent(Event):
    def __init__(self, event):
        Event.__init__(self, event)

    def render(self):
        e = []
        e.append(Paragraph(self.name, styles["pb-event-title"]))
        e.append(Paragraph("%s, <b>%s</b>" % (self.time, self.venue_name), styles["pb-event-venue"]))
        if len(self.place) > 0:
            e.append(Paragraph(self.place, styles["pb-event-venue-address"]))
        e.append(Paragraph(self.description, styles["pb-event-description"]))
        return KeepTogether(e)

# Spacing line with a star
class SpacerLine(Flowable):
    def __init__(self, width, margin):
        Flowable.__init__(self)
        self.width = width
        self.margin = margin
        self.hAlign = "CENTER"
        self.height = 0.5*inch
 
    def draw(self):
        self.canv.saveState()
        self.canv.setLineWidth(0.25)
        self.canv.line(0, self.height/2, self.width/2-15, self.height/2)
        self.canv.setFont("FontAwesome", 11)
        self.canv.drawCentredString(self.width/2, self.height/2-4, u"\uf005")
        self.canv.line(self.width/2+15, self.height/2, self.width, self.height/2)
        self.canv.restoreState()


# Base layout (do not make available to frontend)        
class Layout(object):
    name = "Layout"
    description = ""
    events = 1

    def fill(self, fname, pagesize, events, topspace, bottomspace):
        doc = BaseDocTemplate(fname, pagesize=pagesize, leftMargin=margins, bottomMargin=bottomspace, rightMargin=margins, topMargin=topspace)
        doc.build([])



class TwoColumnLayout(Layout):
    name = "Two Columns (~12 events)"
    description = "A simple two-column layout. This is a good fit if you have around 10 events."
        
    def fill(self, fname, pagesize, events, topspace, bottomspace, margins):
        doc = BaseDocTemplate(fname, pagesize=pagesize, leftMargin=margins, bottomMargin=bottomspace, rightMargin=margins, topMargin=topspace)
        left_column = Frame(doc.leftMargin, doc.bottomMargin, doc.width/2-6, doc.height-0.4*inch, id="left")
        right_column = Frame(doc.leftMargin+doc.width/2+6, doc.bottomMargin, doc.width/2-6, doc.height-0.4*inch, id="right")
        doc.addPageTemplates(PageTemplate(frames=[left_column, right_column]))

        story = []
        for e in events:
            story.append(Event(e).render())
        doc.build(story)


class LargeLayout(Layout):
    name = "Large Events (4-5 events)"
    description = "A layout that presents a small number of events large and in detail. (3-4 events)"
        
    def fill(self, fname, pagesize, events, topspace, bottomspace, margins):
        doc = BaseDocTemplate(fname, pagesize=pagesize, leftMargin=margins, bottomMargin=bottomspace, rightMargin=margins, topMargin=topspace)
        column = Frame(doc.leftMargin, doc.bottomMargin, doc.width-6, doc.height, id="large")
        doc.addPageTemplates(PageTemplate(frames=[column]))

        story = []
        for e in events:
            story.append(XLEvent(e).render())
            story.append(SpacerLine(3*inch, 0))
        story = story[:-1]
        doc.build(story)


class ThreeColumnLayout(Layout):
    name = "Three Columns, extra-tiny events (30+ events)"
    description = "A three-column layout with extra-tiny events. Useful if you need to pack a lot of them " +\
        "into one flyer."
        
    def fill(self, fname, pagesize, events, topspace, bottomspace, margins):
        doc = BaseDocTemplate(fname, pagesize=pagesize, leftMargin=margins, bottomMargin=bottomspace, rightMargin=margins, topMargin=topspace)
        left_column = Frame(doc.leftMargin, doc.bottomMargin, doc.width/3-6, doc.height, id="left")
        middle_column = Frame(doc.leftMargin+doc.width/3+6, doc.bottomMargin, doc.width/3-6, doc.height, id="middle")
        right_column = Frame(doc.leftMargin+2*doc.width/3+6, doc.bottomMargin, doc.width/3-6, doc.height, id="right")
        doc.addPageTemplates(PageTemplate(frames=[left_column, middle_column, right_column]))

        story = []
        for e in events:
            story.append(XSEvent(e).render())
        doc.build(story)

class FeaturedLayout(Layout):
    name = "Feature 1st Event + 2 columns (~10 events)"
    description = "One large main event, and 2 columns with further events."
        
    def fill(self, fname, pagesize, events, topspace, bottomspace, margins):
        doc = BaseDocTemplate(fname, pagesize=pagesize, leftMargin=margins, bottomMargin=bottomspace, rightMargin=margins, topMargin=topspace)
        featured = Frame(doc.leftMargin+0.4*inch, doc.bottomMargin+2*doc.height/3, doc.width-6-0.8*inch,
                doc.height/3-0.4*inch, id="featured")
        left_column = Frame(doc.leftMargin, doc.bottomMargin, doc.width/2-6, 2*doc.height/3, id="left")
        right_column = Frame(doc.leftMargin+doc.width/2+6, doc.bottomMargin, doc.width/2-6, 2*doc.height/3, id="right")
        doc.addPageTemplates(PageTemplate(frames=[featured, left_column, right_column]))

        story = []
        story.append(XLEvent(events[0]).render())
        story.append(SpacerLine(3*inch, 0))
        story.append(FrameBreak())
        for e in events[1:]:
            story.append(Event(e).render())
        doc.build(story)

class PhonebankLayout(Layout):
    events = 1
    name = "Phonebank RSVP Sheet"
    description = "RSVP sheet for a phonebank event."
        
    def fill(self, fname, pagesize, events, topspace, bottomspace, margins):
        std_margin = 0.5*inch
        doc = BaseDocTemplate(fname, pagesize=pagesize, leftMargin=std_margin, bottomMargin=std_margin, rightMargin=std_margin, topMargin=std_margin)
        phonebank = Frame(doc.leftMargin, doc.bottomMargin+3*doc.height/4, doc.width,
                doc.height/4, id="featured")
        doc.addPageTemplates(PageTemplate(frames=[phonebank]))

        story = []
        story.append(PBEvent(events[0]).render())
        story.append(FrameBreak())
        doc.build(story)

class BerniePartyTwoUp(Layout):
    events = 3

    def fill(self, fname, pagesize, events, topspace, bottomspace, margins):
        tf = tempfile.NamedTemporaryFile(delete=False)
        pagesize = (pagesize[0] / 2 - 6, pagesize[1])
        doc = BaseDocTemplate(tf.name, pagesize=pagesize, leftMargin=margins, bottomMargin=bottomspace, rightMargin=margins, topMargin=topspace)
        column = Frame(doc.leftMargin+6, doc.bottomMargin+0.5*inch, doc.width-6, 3.3*inch)
        rsvp = Frame(doc.leftMargin+6, doc.bottomMargin, doc.width-6, 0.5*inch)
        doc.addPageTemplates(PageTemplate(frames=[rsvp, column]))

        # render one side
        story = []
        story.append(Paragraph("Please RSVP at map.berniesanders.com", styles["default"]))
        story.append(FrameBreak())
        for e in events:
            story.append(Event(e).render())
        doc.build(story)

        # now duplicate for 2-up
        src = PdfFileReader(open(tf.name, "rb"))
        out = PdfFileWriter()
        lhs = src.getPage(0)
        lhs.mergeTranslatedPage(lhs, lhs.mediaBox.getUpperRight_x(), 0, True)
        out.addPage(lhs)
        with open(fname.name, "wb") as outfile:
            out.write(outfile)
        os.remove(tf.name)


cached_layouts = None

def layouts():
    global cached_layouts
    if cached_layouts is None:
        cached_layouts = {c.__name__: c for c in Layout.__subclasses__()}
    return cached_layouts

