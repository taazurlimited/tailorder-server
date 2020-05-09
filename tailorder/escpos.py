import time
import serial
from flask.json import loads, dumps
from escpos.printer import File, Usb

from flask import request
from escpos import printer
from bidi.algorithm import get_display
from wand.image import Image as wImage
from wand.drawing import Drawing as wDrawing
from wand.color import Color as wColor
from flask.json import loads
from PIL import Image
import PIL
from pathlib import Path

# Line Width
QTY_WIDTH = 6
ITEM_WIDTH = 26


def write_void(table_no, lines, usb_printer=None, print_item_code=True):
    p = usb_printer if usb_printer else File("/dev/usb/lp0")
    p.text('Table Number: {0}\n'.format(table_no))
    p.text('***VOID ITEMS***\n\n')
    p.text(line_block([
        {'text': 'Item', 'align': '<', 'width': QTY_WIDTH + ITEM_WIDTH}
    ]))

    for line in lines:
        p.text(line_block([
            {'text': line['itemName'], 'align': '<', 'width': QTY_WIDTH + ITEM_WIDTH}
        ]))

        if print_item_code:
            p.text(line_block([
                {'text': line['itemCode'], 'align': '<', 'width': QTY_WIDTH + ITEM_WIDTH}
            ]))

    p.text('\n\nPrinted on:\n')
    p.text(time.ctime())

    p.cut()


def write_additional(table_no, lines, usb_printer=None, print_item_code=True):
    p = usb_printer if usb_printer else File("/dev/usb/lp0")
    p.text('Table Number: {0}\n'.format(table_no))
    p.text('ADDITIONAL ITEMS\n\n')
    p.text(line_block([
        {'text': 'Qty', 'align': '<', 'width': QTY_WIDTH},
        {'text': 'Item', 'align': '<', 'width': ITEM_WIDTH}
    ]))

    for line in lines:
        p.text(line_block([
            {'text': line['qty'], 'align': '<', 'width': QTY_WIDTH},
            {'text': line['itemName'], 'align': '<', 'width': ITEM_WIDTH},
        ]))

        if print_item_code:
            p.text(line_block([
                {'text': '-', 'align': '<', 'width': QTY_WIDTH},
                {'text': line['itemCode'], 'align': '<', 'width': ITEM_WIDTH}
            ]))

    # Time
    p.text('\n\nPrinted on:\n')
    p.text(time.ctime())

    p.cut()


def write_order(order, usb_printer=None, print_item_code=True):
    port_serial = "/dev/rfcomm1"
    home = str(Path.home())
    bluetoothSerial = serial.Serial(port_serial, baudrate=115200, timeout=1)
    company_name = "house_of_spices"
    fontPath = home + "/tailorder-server/fonts/" + company_name + ".ttf"

    tmpImage = 'print_images/kitchen.png'
    printWidth = 570

    height = 450
    draw = wDrawing()
    draw.font = fontPath

    draw.font_size = 30

    y_value = 30
    draw.text(x=5,y=y_value,body="Order Id: ")
    draw.text(x=160,y=y_value,body=str(order.id))

    y_value = y_value + 35
    draw.text(x=5,y=y_value,body="Table Number: ")
    draw.text(x=230,y=y_value,body=str(order.table_no))

    y_value = y_value + 35
    draw.text(x=5,y=y_value,body="Type: ")
    draw.text(x=100,y=y_value,body=str(order.type))

    lines = []
    for i in order.items:
        lines.append(i.__dict__)

    # Headers
    header_line = line_block([
        {'text': 'Qty', 'align': '<', 'width': QTY_WIDTH},
        {'text': 'Item', 'align': '<', 'width': ITEM_WIDTH},
    ])
    y_value = y_value + 45
    draw.text(x=5,y=y_value,body=str(header_line))


    # Lines
    for line in lines:
        line_text = line_block([
            {'text': line['qty'], 'align': '<', 'width': QTY_WIDTH},
            {'text': line['item_name'], 'align': '<', 'width': ITEM_WIDTH},
        ])
        y_value = y_value + 35
        draw.text(x=5,y=y_value,body=str(line_text))

        if print_item_code:
            item_code = line_block([
               {'text': '-', 'align': '<', 'width': QTY_WIDTH},
                {'text': line['item_code'], 'align': '<', 'width': ITEM_WIDTH}
            ])
            y_value = y_value + 35
            draw.text(x=5,y=y_value,body=str(item_code))

    y_value = y_value + 70
    draw.text(x=5,y=y_value,body="Remarks: ")
    draw.text(x=180,y=y_value,body=str(order.remarks))

    y_value = y_value + 70
    draw.text(x=5,y=y_value,body="Printed on: ")
    draw.text(x=180,y=y_value,body=str(time.ctime()))

    im = wImage(width=printWidth, height=height, background=wColor('#ffffff'))
    draw(im)
    im.save(filename=tmpImage)

    #basewidth = 230
    #baseheight = 221
    #logo = "logos/logo.png"
    #img = Image.open(logo)
    #wpercent = (basewidth / float(img.size[0]))
    #img = img.resize((basewidth, baseheight), PIL.Image.ANTIALIAS)
    #img.save(logo)

    # Print an image with your printer library
    printertest = printer.File(port_serial)
    printertest.set(align="center")
    #printertest.image(logo)
    printertest.image(tmpImage)
    printertest.cut()

    bluetoothSerial.close()

def write_order_void(order, usb_printer=None, print_item_code=True):
    if usb_printer:
        p = usb_printer
    else:
        p = File("/dev/usb/lp0")

    lines = []

    for i in order.items:
        lines.append(i.__dict__)

    # Order
    p.text('Void Items')


    # Headers
    header_line = line_block([
        {'text': 'Qty', 'align': '<', 'width': QTY_WIDTH},
        {'text': 'Item', 'align': '<', 'width': ITEM_WIDTH},
    ])

    p.text(header_line)

    # Lines
    for line in lines:
        if line['is_voided']:
            line_text = line_block([
                {'text': line['qty'], 'align': '<', 'width': QTY_WIDTH},
                {'text': line['item_name'], 'align': '<', 'width': ITEM_WIDTH},
            ])
            p.text(line_text)

            if print_item_code:
                item_code = line_block([
                    {'text': '-', 'align': '<', 'width': QTY_WIDTH},
                    {'text': line['item_code'], 'align': '<', 'width': ITEM_WIDTH}
                ])
                p.text(item_code)

    # Time
    p.text('\n\nPrinted on:\n')
    p.text(time.ctime())

    p.cut()
def get_usb(config):
    return Usb(
        config['id_vendor'],
        config['id_product'],
        0,
        config['endpoint_in'],
        config['endpoint_out']
    )


def text_block(text, width, align):
    return '{text:{align}{width}}'.format(text=text, align=align, width=width)


def line_block(contents):
    return ''.join([text_block(c['text'], c['width'], c['align']) for c in contents])
