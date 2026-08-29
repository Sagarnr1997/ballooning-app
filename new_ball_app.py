
import streamlit as st
import tempfile
from pathlib import Path
import base64
import fitz
import copy

from ballooning import balloon_pdf


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Ingenious Engineering - Ballooning Software",
    page_icon="⚙️",
    layout="wide"
)


# ============================================================
# SESSION STATE
# ============================================================

if "balloons" not in st.session_state:
    st.session_state.balloons = []

if "undo_stack" not in st.session_state:
    st.session_state.undo_stack = []

if "redo_stack" not in st.session_state:
    st.session_state.redo_stack = []

if "mode" not in st.session_state:
    st.session_state.mode = "select"

if "generated_pdf" not in st.session_state:
    st.session_state.generated_pdf = None

if "original_pdf" not in st.session_state:
    st.session_state.original_pdf = None

if "total_pages" not in st.session_state:
    st.session_state.total_pages = 0

if "selected_page" not in st.session_state:
    st.session_state.selected_page = 1


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def get_next_id(balloons):
    """Return the next unique balloon ID."""

    if not balloons:
        return 1

    ids = []

    for balloon in balloons:
        try:
            ids.append(int(balloon.get("id", 0)))
        except:
            pass

    return max(ids, default=0) + 1


def renumber_balloons(balloons):
    """Renumber balloons sequentially starting from 1."""

    sorted_balloons = sorted(
        balloons,
        key=lambda b: (
            b.get("page", 1),
            b.get("y", 0),
            b.get("x", 0)
        )
    )

    for index, balloon in enumerate(sorted_balloons, start=1):
        balloon["number"] = index

    return sorted_balloons


def save_undo_state():
    """Save current balloon state for undo."""

    st.session_state.undo_stack.append(
        copy.deepcopy(
            st.session_state.balloons
        )
    )

    # New operation invalidates redo history
    st.session_state.redo_stack = []


def set_background(image_path):

    if not image_path.exists():
        return

    with open(image_path, "rb") as f:
        image_data = base64.b64encode(
            f.read()
        ).decode()

    st.markdown(
        f"""
        <style>

        .stApp {{
            background-image:
                linear-gradient(
                    rgba(3, 15, 38, 0.84),
                    rgba(3, 15, 38, 0.84)
                ),
                url("data:image/png;base64,{image_data}");

            background-size: cover;
            background-position: center;
            background-attachment: fixed;
        }}

        .block-container {{
            padding-top: 1.5rem;
            padding-bottom: 3rem;
            max-width: 1400px;
        }}

        .main-title {{
            text-align: center;
            color: white;
            font-size: 42px;
            font-weight: 700;
            margin-bottom: 5px;
        }}

        .subtitle {{
            text-align: center;
            color: #D9E8FF;
            font-size: 18px;
            margin-bottom: 25px;
        }}

        .preview-title {{
            color: white;
            font-size: 26px;
            font-weight: 700;
            margin-top: 20px;
            margin-bottom: 15px;
        }}

        .toolbar {{
            background: rgba(255,255,255,0.96);
            padding: 15px;
            border-radius: 14px;
            margin-bottom: 15px;
        }}

        .footer {{
            text-align: center;
            color: #D9E8FF;
            margin-top: 40px;
            font-size: 14px;
        }}

        .stButton > button {{
            width: 100%;
            border-radius: 9px;
            font-weight: 600;
        }}

        </style>
        """,
        unsafe_allow_html=True
    )


# ============================================================
# BACKGROUND
# ============================================================

background_path = Path("assets/background.png")

if background_path.exists():
    set_background(background_path)


# ============================================================
# HEADER
# ============================================================

st.markdown(
    """
    <div class="main-title">
        iE INGENIOUS ENGINEERING
    </div>

    <div class="subtitle">
        BALLOONING SOFTWARE
        <br>
        Precise • Intelligent • Efficient
    </div>
    """,
    unsafe_allow_html=True
)


# ============================================================
# UPLOAD DRAWING
# ============================================================

uploaded_file = st.file_uploader(
    "📂 Upload Engineering Drawing PDF",
    type=["pdf"]
)


# ============================================================
# GENERATE BALLOONING
# ============================================================

if uploaded_file:

    st.success(
        f"Uploaded: {uploaded_file.name}"
    )

    if st.button(
        "🚀 Generate Ballooning",
        use_container_width=True
    ):

        with tempfile.TemporaryDirectory() as temp_dir:

            temp_dir = Path(temp_dir)

            input_pdf = (
                temp_dir /
                uploaded_file.name
            )

            output_pdf = (
                temp_dir /
                "ballooned_drawing.pdf"
            )

            # ------------------------------------------------
            # Save uploaded PDF
            # ------------------------------------------------

            with open(input_pdf, "wb") as f:
                f.write(
                    uploaded_file.getbuffer()
                )

            # ------------------------------------------------
            # Generate balloons
            # ------------------------------------------------

            try:

                with st.spinner(
                    "Detecting dimensions and generating balloons..."
                ):

                    result = balloon_pdf(
                        input_pdf,
                        output_pdf
                    )

                # ------------------------------------------------
                # Handle result
                # ------------------------------------------------

                if isinstance(result, int):

                    count = result

                    st.session_state.balloons = []

                elif isinstance(result, dict):

                    count = result.get(
                        "count",
                        0
                    )

                    st.session_state.balloons = (
                        result.get(
                            "balloons",
                            []
                        )
                    )

                else:

                    count = 0

                    st.session_state.balloons = []

                st.success(
                    f"Ballooning completed successfully. "
                    f"{count} dimensions detected."
                )

                # ------------------------------------------------
                # Store generated PDF in session
                # ------------------------------------------------

                with open(output_pdf, "rb") as f:
                    st.session_state.generated_pdf = (
                        f.read()
                    )

                with open(input_pdf, "rb") as f:
                    st.session_state.original_pdf = (
                        f.read()
                    )

                # ------------------------------------------------
                # Determine pages
                # ------------------------------------------------

                pdf_document = fitz.open(
                    stream=st.session_state.generated_pdf,
                    filetype="pdf"
                )

                st.session_state.total_pages = (
                    len(pdf_document)
                )

                st.session_state.selected_page = 1

                pdf_document.close()

                # ------------------------------------------------
                # Reset editing history
                # ------------------------------------------------

                st.session_state.undo_stack = []
                st.session_state.redo_stack = []
                st.session_state.mode = "select"

            except Exception as e:

                st.error(
                    f"Ballooning failed: {e}"
                )


# ============================================================
# EDITOR
# ============================================================

if st.session_state.generated_pdf:

    st.markdown(
        """
        <div class="preview-title">
            📐 Balloon Editor
        </div>
        """,
        unsafe_allow_html=True
    )


    # ========================================================
    # TOOLBAR
    # ========================================================

    st.markdown(
        '<div class="toolbar">',
        unsafe_allow_html=True
    )

    col1, col2, col3, col4, col5, col6, col7 = st.columns(7)


    # --------------------------------------------------------
    # SELECT
    # --------------------------------------------------------

    with col1:

        if st.button(
            "🔍 Select",
            use_container_width=True
        ):

            st.session_state.mode = "select"


    # --------------------------------------------------------
    # ADD
    # --------------------------------------------------------

    with col2:

        if st.button(
            "➕ Add Balloon",
            use_container_width=True
        ):

            st.session_state.mode = "add"


    # --------------------------------------------------------
    # DELETE
    # --------------------------------------------------------

    with col3:

        if st.button(
            "🗑 Delete",
            use_container_width=True
        ):

            st.session_state.mode = "delete"


    # --------------------------------------------------------
    # MOVE
    # --------------------------------------------------------

    with col4:

        if st.button(
            "✋ Move",
            use_container_width=True
        ):

            st.session_state.mode = "move"


    # --------------------------------------------------------
    # RENUMBER
    # --------------------------------------------------------

    with col5:

        if st.button(
            "🔄 Renumber",
            use_container_width=True
        ):

            if st.session_state.balloons:

                save_undo_state()

                st.session_state.balloons = (
                    renumber_balloons(
                        st.session_state.balloons
                    )
                )

                st.success(
                    "Balloon numbers corrected."
                )

                st.rerun()


    # --------------------------------------------------------
    # UNDO
    # --------------------------------------------------------

    with col6:

        if st.button(
            "↶ Undo",
            use_container_width=True
        ):

            if st.session_state.undo_stack:

                st.session_state.redo_stack.append(
                    copy.deepcopy(
                        st.session_state.balloons
                    )
                )

                st.session_state.balloons = (
                    st.session_state.undo_stack.pop()
                )

                st.rerun()

            else:

                st.info(
                    "Nothing to undo."
                )


    # --------------------------------------------------------
    # REDO
    # --------------------------------------------------------

    with col7:

        if st.button(
            "↷ Redo",
            use_container_width=True
        ):

            if st.session_state.redo_stack:

                st.session_state.undo_stack.append(
                    copy.deepcopy(
                        st.session_state.balloons
                    )
                )

                st.session_state.balloons = (
                    st.session_state.redo_stack.pop()
                )

                st.rerun()

            else:

                st.info(
                    "Nothing to redo."
                )


    st.markdown(
        '</div>',
        unsafe_allow_html=True
    )


    # ========================================================
    # CURRENT MODE
    # ========================================================

    mode_names = {

        "select":
            "🔍 SELECT MODE",

        "add":
            "➕ ADD BALLOON MODE",

        "delete":
            "🗑 DELETE BALLOON MODE",

        "move":
            "✋ MOVE BALLOON MODE"
    }

    st.info(
        f"Current Tool: "
        f"**{mode_names[st.session_state.mode]}**"
    )


    # ========================================================
    # PAGE SELECTION
    # ========================================================

    total_pages = st.session_state.total_pages

    if total_pages > 1:

        selected_page = st.number_input(
            "Drawing Page",
            min_value=1,
            max_value=total_pages,
            value=st.session_state.selected_page,
            step=1
        )

        st.session_state.selected_page = (
            int(selected_page)
        )

    else:

        selected_page = 1


    # ========================================================
    # OPEN PDF
    # ========================================================

    pdf_document = fitz.open(
        stream=st.session_state.generated_pdf,
        filetype="pdf"
    )

    page = pdf_document[
        int(selected_page) - 1
    ]


    # ========================================================
    # RENDER DRAWING
    # ========================================================

    zoom = 2.0

    matrix = fitz.Matrix(
        zoom,
        zoom
    )

    pix = page.get_pixmap(
        matrix=matrix,
        alpha=False
    )

    image_bytes = pix.tobytes(
        "png"
    )


    # ========================================================
    # DRAWING PREVIEW
    # ========================================================

    st.image(
        image_bytes,
        caption=(
            f"Ballooned Drawing - "
            f"Page {selected_page}"
        ),
        width="stretch"
    )


    # ========================================================
    # BALLOON MANAGEMENT
    # ========================================================

    st.markdown(
        """
        <div class="preview-title">
            🎈 Balloon Management
        </div>
        """,
        unsafe_allow_html=True
    )


    left, right = st.columns([2, 1])


    # ========================================================
    # BALLOON LIST
    # ========================================================

    with left:

        balloons = st.session_state.balloons

        if balloons:

            balloon_options = []

            for balloon in balloons:

                balloon_options.append(
                    f"Balloon {balloon.get('number', '?')} "
                    f"- Dimension "
                    f"{balloon.get('dimension_text', '')}"
                )

            selected_balloon_label = st.selectbox(
                "Select Balloon",
                balloon_options
            )

            selected_index = (
                balloon_options.index(
                    selected_balloon_label
                )
            )

            selected_balloon = balloons[
                selected_index
            ]

        else:

            st.warning(
                "No editable balloon information "
                "is available."
            )

            st.info(
                "Your balloon_pdf() function currently "
                "returns only the balloon count. "
                "To enable editing, balloon_pdf() should "
                "return balloon information."
            )

            selected_balloon = None


    # ========================================================
    # EDIT CONTROLS
    # ========================================================

    with right:

        if balloons:

            st.metric(
                "Total Balloons",
                len(balloons)
            )

            st.metric(
                "Current Balloon",
                selected_balloon.get(
                    "number",
                    "-"
                )
            )


            # ------------------------------------------------
            # DELETE SELECTED BALLOON
            # ------------------------------------------------

            if st.button(
                "🗑 Delete Selected Balloon",
                use_container_width=True
            ):

                save_undo_state()

                dimension_id = (
                    selected_balloon.get(
                        "dimension_id"
                    )
                )

                st.session_state.balloons = [

                    b for b in
                    st.session_state.balloons

                    if b.get("dimension_id")
                    != dimension_id

                ]

                st.session_state.balloons = (
                    renumber_balloons(
                        st.session_state.balloons
                    )
                )

                st.success(
                    "Balloon deleted and "
                    "numbers automatically corrected."
                )

                st.rerun()


    # ========================================================
    # ADD BALLOON
    # ========================================================

    if st.session_state.mode == "add":

        st.markdown(
            "### ➕ Add Missing Balloon"
        )

        st.write(
            "Select an existing dimension and create "
            "an additional balloon for it."
        )

        if balloons:

            dimensions = [

                b.get(
                    "dimension_text",
                    ""
                )

                for b in balloons

            ]

            dimension_to_add = st.selectbox(
                "Dimension",
                dimensions,
                key="add_dimension"
            )

            if st.button(
                "➕ Add Balloon to Dimension",
                use_container_width=True
            ):

                save_undo_state()

                source = None

                for b in balloons:

                    if (
                        b.get("dimension_text")
                        == dimension_to_add
                    ):

                        source = b
                        break

                if source:

                    new_balloon = {

                        "id":
                            get_next_id(
                                balloons
                            ),

                        "dimension_id":
                            source.get(
                                "dimension_id"
                            ),

                        "dimension_text":
                            source.get(
                                "dimension_text",
                                ""
                            ),

                        "page":
                            source.get(
                                "page",
                                1
                            ),

                        "x":
                            source.get(
                                "x",
                                0
                            ) + 80,

                        "y":
                            source.get(
                                "y",
                                0
                            )
                    }

                    st.session_state.balloons.append(
                        new_balloon
                    )

                    st.session_state.balloons = (
                        renumber_balloons(
                            st.session_state.balloons
                        )
                    )

                    st.success(
                        "Balloon added successfully."
                    )

                    st.rerun()


    # ========================================================
    # POSITIONING
    # ========================================================

    if st.session_state.mode == "move":

        st.markdown(
            "### ✋ Balloon Positioning"
        )

        if balloons:

            selected_move = st.selectbox(
                "Select Balloon to Move",
                [
                    f"Balloon {b.get('number', '?')}"
                    for b in balloons
                ],
                key="move_balloon"
            )

            try:

                selected_number = int(
                    selected_move.split()[-1]
                )

                selected_move_balloon = next(
                    b for b in balloons
                    if b.get("number")
                    == selected_number
                )

            except:

                selected_move_balloon = balloons[0]


            col_x, col_y = st.columns(2)


            with col_x:

                new_x = st.number_input(
                    "X Position",
                    value=float(
                        selected_move_balloon.get(
                            "x",
                            0
                        )
                    ),
                    step=5.0
                )


            with col_y:

                new_y = st.number_input(
                    "Y Position",
                    value=float(
                        selected_move_balloon.get(
                            "y",
                            0
                        )
                    ),
                    step=5.0
                )


            if st.button(
                "📍 Update Balloon Position",
                use_container_width=True
            ):

                save_undo_state()

                selected_move_balloon["x"] = new_x
                selected_move_balloon["y"] = new_y

                st.success(
                    "Balloon position updated."
                )

                st.rerun()


    # ========================================================
    # VALIDATION
    # ========================================================

    st.markdown(
        """
        <div class="preview-title">
            🔍 Balloon Validation
        </div>
        """,
        unsafe_allow_html=True
    )


    balloons = st.session_state.balloons


    if balloons:

        numbers = [

            b.get(
                "number"
            )

            for b in balloons

        ]


        expected_numbers = list(
            range(
                1,
                len(numbers) + 1
            )
        )


        numbering_ok = (
            numbers
            == expected_numbers
        )


        dimension_ids = [

            b.get(
                "dimension_id"
            )

            for b in balloons

        ]


        duplicate_dimensions = (

            len(dimension_ids)
            != len(
                set(
                    dimension_ids
                )
            )

        )


        c1, c2, c3 = st.columns(3)


        with c1:

            st.metric(
                "Total Balloons",
                len(balloons)
            )


        with c2:

            if numbering_ok:

                st.success(
                    "✓ Numbering Correct"
                )

            else:

                st.error(
                    "✗ Numbering Error"
                )


        with c3:

            if duplicate_dimensions:

                st.error(
                    "✗ Duplicate Dimension"
                )

            else:

                st.success(
                    "✓ No Duplicate Dimensions"
                )


    # ========================================================
    # FINAL PDF
    # ========================================================

    st.markdown(
        """
        <div class="preview-title">
            💾 Final Drawing
        </div>
        """,
        unsafe_allow_html=True
    )


    if st.button(
        "🔄 Apply Changes & Generate Final PDF",
        use_container_width=True
    ):

        st.warning(
            "Balloon position/list changes are currently "
            "stored in session state. To permanently "
            "apply edited balloon positions to the PDF, "
            "ballooning.py must provide a renderer that "
            "accepts st.session_state.balloons."
        )


    # ========================================================
    # DOWNLOAD
    # ========================================================

    st.download_button(
        label="⬇️ Download Ballooned PDF",
        data=st.session_state.generated_pdf,
        file_name="ballooned_drawing.pdf",
        mime="application/pdf",
        use_container_width=True
    )


    pdf_document.close()


# ============================================================
# FOOTER
# ============================================================

st.markdown(
    """
    <div class="footer">

        <b>iE Ingenious Engineering</b>

        <br>

        Engineering Drawing Automation

        <br><br>

        Accurate Ballooning • Automated Dimension Detection •
        Inspection Ready Reports

    </div>
    """,
    unsafe_allow_html=True
)

