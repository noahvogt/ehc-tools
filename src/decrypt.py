#!/usr/bin/env python3
import json, sys, zlib, base45, cbor2, optparse, os


def checkFilePath(file):
    if not( os.path.isfile(file) and os.access(file, os.R_OK)):
        print('Error: File does not exist or is not readable/accessable')
        exit()

def getSecondParameter(shortOption, longOption):
    successIndex = -10 # arbitrary number to check for changes later
    args = sys.argv
    for i in range((len(args))):
        if args[i] == shortOption or args[i] == longOption:
            successIndex = i + 1
            break
    if successIndex == -10 or successIndex + 1 > len(args):
        print("Error: Please enter valid i/o parameters\nHint: run 'python decrypt.py -h'")
        exit(1)
    else:
        return args[successIndex]

def parseCommandlineArguments():
    global options
    global verboseMode

    # define cli options
    cli_parser = optparse.OptionParser()
    cli_parser.set_defaults(debug=False)
    cli_parser.add_option('-v', '--verbose', action='store_true', dest='verbose',
        help='prints status messages to stdout')
    cli_parser.add_option('-i', '--image', action='store_true', dest='image',
        help='specify an image as input with the next argument')
    cli_parser.add_option('-t', '--text', action='store_true', dest='text',
        help='specify text as input with the next argument')
    cli_parser.add_option('-f', '--file', action='store_true', dest='file',
        help='specify a text file as input with the next argument')
    (options, args) = cli_parser.parse_args()

    # check for verbose mode
    if options.verbose:
        verboseMode = True
        print('[Verbose:] verbose mode activated')
    else:
        verboseMode = False

def getQRcode():
    if options.image and options.text is None and options.file is None:
        imageName = getSecondParameter('-i', '--image')
        checkFilePath(imageName)

        from pyzbar.pyzbar import decode
        from PIL import Image

        try:
            img = Image.open(imageName)
            decode = decode(img.convert('RGBA')) # convert to RBGA image to avoid PIL warning
            return decode[0].data.decode('ascii')
        except:
            print("Error: Error while opening your image. Are you sure it is actually a QR Code?")
            exit()
    elif options.text and options.image is None and options.file is None:
        return getSecondParameter('-t', '--text')
    elif options.file and options.image is None and options.text is None:
        fileName = getSecondParameter('-f', '--file')
        checkFilePath(fileName)

        with open(fileName, 'r') as fileopener:
            return fileopener.read()
    else:
        print("Error: Please specify (only one!) qr code i/o argument\nHint: run 'python decrypt.py -h'")
        exit(1)

def stripIdentifiers(qrdata):
    # remove Context Identifier string (usually 'HCI:'), for more information check the official specification:
    # https://github.com/ehn-dcc-development/hcert-spec/blob/main/hcert_spec.md#422-qr-2d-barcode
    qrdata = qrdata[qrdata.find(':') + 1:]
    verbosePrint('raw QR code data', qrdata)
    return qrdata

def decryptPayload(qrdata):
    try:
        base45data = base45.b45decode(str(qrdata))
        verbosePrint('Base45 decoded data', base45data)
        zlibdata = zlib.decompress(base45data)
        verbosePrint('Zlib decompressed data', base45data)
        cosedata = cbor2.loads(zlibdata)
        verbosePrint("COSE 'sign1' signed data", cosedata)
        payload = cbor2.loads(cosedata.value[2])
    except:
        print("Error: Error while decrypting your string. Are you sure you entered it correctly?")
        exit(1)
    return payload

def verbosePrint(desc, text):
    if verboseMode: print("\n[Verbose:] {}\n{}".format(desc, text))

def printPayload(payload):
    prettyPayload = json.dumps(payload, indent=4, sort_keys=True, ensure_ascii=False).encode('utf8')
    if verboseMode: print('\n[Verbose:] formatted JSON data')
    print(prettyPayload.decode())


def main():
    parseCommandlineArguments()
    qrcode = stripIdentifiers(getQRcode())

    printPayload(decryptPayload(qrcode))

if __name__ == "__main__":
    main()
