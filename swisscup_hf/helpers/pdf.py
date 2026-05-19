import pandas as pd
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Flowable, Paragraph, Spacer
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Image
from reportlab.lib.utils import ImageReader
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.colors import grey
from helpers.config import LOGO_PATH, INFO_TEXT

def add_data_to_lists(overall_rows: list, gender_rows: list, athlete_data: dict, competitions: list, civil_id):
    row = {
        "name": f"{athlete_data['first_name']} {athlete_data['name']}",
        }
    for comp in competitions:
        try:
           row[comp] = athlete_data["competitions"][comp]["points"]
        except KeyError:
           row[comp] = ""
    row["total_points"] = athlete_data["total_points"]
    row["civil_id"] = civil_id
    row["gender"] = athlete_data["gender"]
    row["nat"] = athlete_data["nat"]
    row["glider"] = athlete_data["glider"]

    # add the data row to the lists
    overall_rows.append(row), gender_rows.append(row)

    return overall_rows, gender_rows


def generate_pandas_data_frames(json_data: dict, all_competitions: list):
    rows_female = []
    rows_male = []
    rows_overall = []
    for civl_id in json_data.keys():
        if json_data[civl_id]['gender'] == 'F':
            rows_overall, rows_female = add_data_to_lists(rows_overall, rows_female, json_data[civl_id], all_competitions, civl_id)
        else:
            rows_overall, rows_male = add_data_to_lists(rows_overall, rows_male, json_data[civl_id], all_competitions, civl_id)

    df_female = pd.DataFrame(rows_female)
    df_male = pd.DataFrame(rows_male)
    df_overall = pd.DataFrame(rows_overall)

    return df_female, df_male, df_overall


def extract_competition_name_list(competition_json: dict):
    names = []
    for comp in competition_json.keys():
        names.append(competition_json[comp]["title"])
    return names



class RotatedHeader(Flowable):
    def __init__(self, text, width=40, height=60, fontSize=10):
        super().__init__()
        self.text = text
        self.width = width
        self.height = height
        self.fontSize = fontSize

    def draw(self):
        self.canv.saveState()
        self.canv.setFont("Helvetica-Bold", self.fontSize)

        # Move origin to the bottom center of the cell
        self.canv.translate(0, 0)

        # Rotate around the new origin
        self.canv.rotate(90)

        # Draw string so it's centered and touches bottom
        text_width = self.canv.stringWidth(self.text, "Helvetica", self.fontSize)
        self.canv.drawString(5 , -24, self.text) # the first number aligns up/down, smaller -> down, secon number moves left/rigth, smaller -> right, but they also influence each other

        self.canv.restoreState()

    def wrap(self, availWidth, availHeight):
        return self.width, self.height




def generate_single_pdf(json_data: dict, competition_json: dict, df: pd.DataFrame, titel: str, path: str):
    doc = SimpleDocTemplate(str(path), pagesize=landscape(A4), leftMargin=20, rightMargin=20, topMargin=30, bottomMargin=20)

    styles = getSampleStyleSheet()
    story = []

    # Load and resize image with preserved aspect ratio
    img_reader = ImageReader(LOGO_PATH)
    orig_width, orig_height = img_reader.getSize()
    target_width = 100
    aspect_ratio = orig_height / orig_width
    target_height = target_width * aspect_ratio
    logo = Image(LOGO_PATH, width=target_width, height=target_height)

    # Create title paragraph
    title_para = Paragraph(f"<b>{titel}</b>", styles["Title"])

    # Create a 1-row, 2-column table with logo and title
    title_table = Table([[title_para, logo]], colWidths=[400, target_width + 10])  # Adjust second colWidth as needed
    title_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (1, 0), (1, 0), "LEFT"),  # Align title left if desired
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))

    # Add to story
    story.append(title_table)
    story.append(Spacer(1, 12))

    # add infos, so called "Kleingedrucktes"
    # Create a custom small grey text style
    info_style = ParagraphStyle(
        name="InfoStyle",
        parent=styles["Normal"],
        fontSize=8,
        textColor=grey,
        spaceBefore=2,
        spaceAfter=2,
    )

    story.append(Paragraph(INFO_TEXT, info_style))

    # Prepare table header
    competitions = extract_competition_name_list(competition_json)
    raw_header = ["Rank", "Civil ID", "Name", "Gender", "Nationality", "Glider"] + competitions + ["Total Points"]
    header = []

    for i, col in enumerate(raw_header):
         header.append(RotatedHeader(col))

    # Prepare table rows
    table_data = [header]
    highlight_cells = []
    previous_points = 0
    pervious_rank = 0
    for rank, (idx, row) in enumerate(df.iterrows(), 1):
        if row["total_points"] == previous_points:
            athletes_true_rank = pervious_rank
        else:
            athletes_true_rank = rank
            previous_points = row["total_points"]
            pervious_rank = rank
        row_data = [str(athletes_true_rank), row["civil_id"], row["name"], row["gender"], row["nat"], row["glider"]]

        for offset, comp_key in enumerate(competition_json.keys()):
            row_data.append(str(row[comp_key]))

            try:
              # If this comp counts for the athlete, store (row_index, col_index) for highlighting
              if json_data[row["civil_id"]]["competitions"][comp_key]["counts"]:
                  table_row_idx = len(table_data)  # current row index in table
                  table_col_idx = 6 + offset     # offset by Rank and Name, gender, nat, glider columns
                  highlight_cells.append((table_row_idx, table_col_idx))
            except KeyError:
              continue

        row_data.append(str(row.get("total_points", "")))
        table_data.append(row_data)

    # Build the table
    col_widths = [20, 40, 135, 20, 30, 140] + [30] * len(competitions) + [35]
    row_heights = [155] + [None] * (len(table_data) - 1)
    table = Table(table_data, colWidths=col_widths, rowHeights=row_heights, repeatRows=1)

    style = TableStyle([
        # Basic grid
        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),

        # Header styling
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),

        # Body alignment

      ("ALIGN", (0, 1), (0, -1), "CENTER"),  # Rank
      ("ALIGN", (1, 1), (1, -1), "LEFT"),    # Civil id
      ("ALIGN", (2, 1), (2, -1), "LEFT"),    # Name
      ("ALIGN", (3, 1), (4, -1), "CENTER"),  # Gender and Nationality
      ("ALIGN", (5, 1), (5, -1), "LEFT"),    # Glider
      ("ALIGN", (6, 1), (-1, -1), "CENTER"), # Competitions + Total Points


        # Bold outer border
        ("BOX", (0, 0), (-1, -1), 1.5, colors.black),

        # Bold line after header row
        ("LINEBELOW", (0, 0), (-1, 0), 1.5, colors.black),

        # Bold vertical line after sixth column (Glider)
        ("LINEAFTER", (5, 0), (5, -1), 1.5, colors.black),

        # Bold vertical line before last column (Total Points)
        ("LINEBEFORE", (-1, 0), (-1, -1), 1.5, colors.black),
    ])

    highlight_color = colors.Color(red=172/255, green=220/255, blue=149/255, alpha = 0.6)


    # Light grey background for alternating rows (excluding header)
    for i in range(1, len(table_data)):
        if i % 2 == 0:  # Even-numbered row (index starts at 0)
            style.add("BACKGROUND", (0, i), (-1, i), colors.whitesmoke)

    for r, c in highlight_cells:
        style.add("BACKGROUND", (c, r), (c, r), highlight_color)

    table.setStyle(style)

    story.append(table)
    doc.build(story)
