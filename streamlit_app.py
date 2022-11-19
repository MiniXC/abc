import streamlit as st
from streamlit_quill import st_quill
from html2image import Html2Image
from poooli import Poooli
from PIL import Image
import numpy as np
from time import sleep
import pymongo
import io
from pathlib import Path

hti = Html2Image(output_path='screenshots')
pli = Poooli()

st.header("ABC (Advanced Babbi Interface)")

with st.sidebar:
    st.header("Options")
    color = st.radio(
        "Color Mode",
        options=["Black & White (Dither)", "Black & White (Threshold)"],
        key='color_mode',
    )
    brightness = st.slider('Brightness Modifier', 0., 2., 1., 0.1)
    contrast = st.slider('Contrast Modifier', 0., 2., 1., 0.1)
    max_height = st.slider('Maximum Height', 100, 2000, 1000, 100)
    show_html = st.checkbox('Show HTML', key='show_html')

content = st_quill(
    html=True,
    key='text_editor',
    toolbar=[
            [
                "bold", "italic", "underline", "strike",
                {"script": "sub"},
                {"script": "super"},
            ],
            [
                {"background": []},
                {"color": [] },
            ],          
            [
                {"list": "ordered"},
                {"list": "bullet"},
                {"indent": "-1"},
                {"indent": "+1"},
                {"align": []},
            ],
            [
                {"header": 1},
                {"header": 2},
                {"header": [1, 2, 3, 4, 5, 6, False]},
                {"size": ["small", False, "large", "huge"]},
            ],
            [
                "blockquote", "clean"
            ],
            [
                "image"
            ],
            [
                {"font": []}
            ],
        ]
)

# if st.button("Preview"):
if show_html:
    st.write(content)

if content != "<p><br></p>" and content != "":
    Path("screenshots").mkdir(parents=True, exist_ok=True)
    with st.spinner("Processing Image..."):
        hti.screenshot(
            html_str=content, 
            css_str="""
                body {background: white; font-size: 1.5em; font-family: sans-serif;}
                body img {max-width: 100%;}
                .ql-align-right {text-align: right;}
                .ql-align-center {text-align: center;}
                .ql-align-justify {text-align: justify;}
                .ql-font-monospace {font-family: monospace;}
                .ql-font-serif {font-family: serif;}
                .ql-font-sans-serif {font-family: sans-serif;}
                .ql-size-small {font-size: 0.75em;}
                .ql-size-large {font-size: 1.5em;}
                .ql-size-huge {font-size: 2.5em;}
            """,
            css_file="css/pico.classless.min.css",
            size=(384, max_height), 
            save_as='editor.png',
        )
        if "Dither" in color:
            mode = "bnw_dither"
        else:
            mode = "bnw"
        img = pli.process_image('screenshots/editor.png', mode=mode, brightness=brightness, contrast=contrast)
        np_img = np.asarray(img)
        end_i = None
        for i in reversed(list(range(len(np_img)))):
            if False in np_img[i]:
                end_i = i
                break
        if end_i is not None:
            np_img = np_img[:end_i+2]
        img = Image.fromarray(np_img)

    with st.form(key="send_form"):
        st.image(img, use_column_width="always")
        to = st.selectbox(
            "Send to...",
            options=["Cécé", "Stouf"],
            key='send_to',
        )
        submitted = st.form_submit_button(label='Send')
        if submitted:
            pwd = st.secrets["DB_PASSWORD"]
            client = pymongo.MongoClient(f"mongodb+srv://root:{pwd}@cece.ldq20.mongodb.net/?retryWrites=true&w=majority")
            db = client.cece
            messages = db.messages
            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format='PNG')
            img_byte_arr = img_byte_arr.getvalue()
            msg_result = messages.insert_one({"for": to, "image": img_byte_arr, "printed": False})
            st.success("Sent, waiting for response!")
            _id = msg_result.inserted_id
            with st.spinner("Waiting for response..."):
                msg_printed = False
                i = 0
                while not msg_printed:
                    sleep(1)
                    msg_printed = messages.find_one({"_id": _id})["printed"]
                    if msg_printed:
                        st.success("Message printed!")
                        break
                    else:
                        i += 1
                    if i > 5:
                        st.error("No response, try again later.")
                        break
            messages.delete_one({"_id": _id})