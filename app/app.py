from flask import Flask, request, jsonify, render_template, send_from_directory, flash, redirect
from werkzeug.utils import secure_filename
from flask import make_response
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_mail import Mail
from flask_mail import Message
from wallet.models import Pass, Barcode, Generic
import hashlib
from pushjack import APNSClient
import os
import logging
import json
from datetime import datetime
import shutil
import pandas as pd
from pytz import timezone
import csv

# from queue import Queue
# import threading


app = Flask(__name__)
app.config.from_object(os.environ['APP_SETTINGS'])

# Other Application Configuerations
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = os.environ['SERVER_EMAIL']
app.config['MAIL_PASSWORD'] = os.environ['SERVER_EMAIL_PASSWORD']
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
app.config['PASS_FOLDER'] = './pkpass files'
app.config['CERTIFICATES_FOLDER'] = './certificates'
app.config['UPLOAD_FOLDER'] = './last membership'
mail = Mail(app)
db = SQLAlchemy(app)
ma = Marshmallow(app)
ALLOWED_EXTENSIONS = set(['csv'])

# Configure logging
logging.basicConfig(level=logging.DEBUG,
                    format='[%(levelname)s] - %(threadName)-10s : %(message)s')

from models import Member, Card, Device, member_card_association, registration

if __name__ == "__main__":
    # Only for debugging while developing
    app.run(host='0.0.0.0', debug=True)


# ERROR HANDLERS
@app.errorhandler(404)
def not_found(error):
    logging.debug(request)
    logging.debug(error)
    return make_response(jsonify({'error': 'Not found'}), 404)


@app.errorhandler(400)
def not_found(error):
    logging.debug(error)
    return make_response(jsonify({'error': 'Bad request'}), 400)


@app.errorhandler(401)
def not_authorized(error):
    logging.debug(error)
    return make_response(jsonify({'error': 'Unauthorized'}), 401)


# MAIN ROUTES

# Main Dashboard
# GET phippsconservatory.xyz/, phippsconservatory.xyz/index.html
@app.route("/", methods=['GET'])
@app.route("/index.html", methods=['GET'])
def index():
    members = Member.query.all()
    passes = Card.query.all()
    devices = Device.query.all()
    return render_template('index.html', memberCnt=len(members), passCnt=len(passes), deviceCnt=len(devices),
                           pendingCnt=0)


# Upload membership.csv file
# GET phippsconservatory.xyz/upload_membership
@app.route("/upload_membership", methods=['GET', 'POST'])
def upload_membership():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            return jsonify({'count': 0})
        file = request.files['file']
        # if user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            # last_member.csv is the last uploaded
            # filename is current file being uploaded name
            # find_differnce creates a update.csv, the difference
            # between the two files.
            count = 0
            if find_difference(filename):
                count = insertUpdate()
                os.remove(os.path.join(app.config['UPLOAD_FOLDER'], "update.csv"))
            else:
                return jsonify({'count': 0})
                logging.debug("Difference wasn't properly calculated!")
        # return render_template('upload_membership.html')
        return jsonify({'count': count})
    # return jsonify({'error': 0})
    return render_template('upload_membership.html')


# Send Pass page
# GET phippsconservatory.xyz/send_pass
@app.route("/send_pass", methods=['GET'])
def send_passes():
    data = db.session.query(Member, Card, Device).join(member_card_association).join(Card).outerjoin(
        registration).outerjoin(Device).all();
    return render_template('send_passes.html', data=data)


# Send mail containing pass to member
# POST phippsconservatory.xyz/send_mail
@app.route('/send_mail', methods=['POST'])
def send_mail():
    recipient_email = request.values.get('email', None)
    name = request.values.get('name', None)
    authtok = request.values.get('authtok', None)
    msg = Message("Digital Membership Card | Phipps Conservatory and Botanical Gardens",
                  sender="georgeY852@gmail.com",
                  recipients=["georgeY852@gmail.com"]) # recipient_email
    msg.html = '''
        Dear {},<br><br>
        Phipps Conservatory is continuing it's
        mission of reducing our carbon footprint. One of our new initiatives
        is providing members with their membership cards available digitally within your phone. Attached to this
        email is your membership card that can be saved and loaded onto your devices.<br><br>
        For Apple devices:
        <ul>
            <li> If you're opening this email on your iPhone, simply double tap on the attached .pkpass file, and it 
            should prompt you to add your new membership pass to the 'Wallet' Application (available by default on all
            iPhone devices). On the top right, tap on 'Add'.<br>
            <li> If you're on your MacBook, you can also double click on the attached file for it to be added to all
             your Apple devices.
            <br>
            NOTE: This will only work if you've connected your iPhone and MacBook with the same iCloud. If not, you can
             download your .pkpass file, and 'Airdrop' it to your iPhone.
        </ul>
        For Android phones:<br>
        <ul>
            <li> Go to the Google Play Store, and install the application 'Passes'<br>
            <li> Once 'Passes' is installed, double tap on the attached .pkpass file. You will be asked which application
             to choose from to open this file. Tap on 'Passes', and your membership card will automatically be added.<br>
        </ul>
        <br>
        For Windows Computers:
        <ul>
            <li> If you have an iPhone, but not a MacBook, you will have to first need to have iTunes installed on your computer.
            This is needed in order to safely transfer files between your computer to your iphone safely. 
            <br>
            <li> Download the .pkpass file attached onto your computer. 
            <br>
            <li> Connect your iPhone to your computer via the provided charging cable. This should automatically open up
            iTunes; if not, open iTunes.
            <br>
            <li> In iTunes click on the 'Device' button, then click on 'File Sharing' in the sidebar. You should be able to 
            see a list of applications that can transfer files from your computer to your phone. Click on one, and
            then find the .pkpass file in your downloads folder. Finally click on 'Sync' to transfer the .pkpass file to your
            iPhone.
            <br>
        </ul>
        
        This digital membership pass is available for use even when your device is not connected to the Internet, 
        and thus can be used at anytime after saving to your phone. Updates to your membership will be reflected on the next business day,
         and will require access to the Internet. <br>
        We hope to see you visit again soon!<br><br>
        Mike Cassidy<br>
        Membership Administrator<br>
        412/622-6915, ext. 6500<br>
        mcassidy@phipps.conservatory.org<br>
        <img src='https://i.ibb.co/q5QrGXf/phipps-email-logo.png'><br>
        <font color="#78a22f">Phipps Conservatory and Botanical Gardens</font><br>
        <font color="#78a22f">One Schenley Park</font><br>
        <font color="#78a22f">Pittsburgh, Pa. 15213</font><br>
        <font color="#78a22f"><a href="phipps.conservatory.org"></font><br>
        <font color="#78a22f"><a href="facebook.com/phippsconservatory"></font><br>
        <font color="#78a22f"><a href="twitter.com/phippsnews"></font>
        '''.format(name.split()[0])

    filename = "{}.pkpass".format(name.replace(" ", ""))
    with app.open_resource("pkpass files/{}".format(filename)) as fp:
        msg.attach("{}".format(filename), "pkpass files/{}".format(filename), fp.read())
    mail.send(msg)
    aPass = Card.query.filter_by(authenticationToken=authtok).first()

    if aPass is not None:
        aPass.last_sent = datetime.now().astimezone(timezone('EST5EDT')).strftime("%Y-%m-%dT%H:%M:%S")
        db.session.add(aPass)
        db.session.commit()
        return jsonify({'Status': 'Success'})
    else:
        return jsonify({'Status': 'Fail'})



# Registering Device to Receive Push Notifications for future updates for a pass
# POST phippsconservatory.xyz/v1/devices/<deviceLibraryIdentifier>/registrations/pass.org.conservatory.phipps.membership/<serialNumber>
@app.route("/<version>/devices/<deviceLibraryIdentifier>/registrations/<passTypeIdentifier>/<serialNumber>",
           methods=['POST'])
def register_device(version, deviceLibraryIdentifier, passTypeIdentifier, serialNumber):
    recievedAuth = request.headers.get('Authorization').split(" ")[1]
    aPass = Card.query.filter_by(id=serialNumber).first()
    # Verify that version and pass type ID is correct,
    # that serial number on pass exists, and the
    # authentication token is correct
    # If not, return 401 Unauthorized
    if (version != 'v1') or (passTypeIdentifier != 'pass.org.conservatory.phipps.membership') or (aPass is None) \
            or (aPass.authenticationToken != recievedAuth):
        return not_authorized("Device registration could not be completed.")
    else:
        # Check if device is already registered, and if not
        # then register device
        if db.session.query(Device).filter((Device.device_lib_id == deviceLibraryIdentifier)
                                           & (Device.push_token == request.values.get('pushToken'))).first() is None:
            newDevice = Device(
                date_registered=datetime.now().astimezone(timezone('EST5EDT')).strftime("%Y-%m-%dT%H:%M:%S"),
                device_lib_id=deviceLibraryIdentifier,
                push_token=request.get_json().get('pushToken'))
            aPass.devices.append(newDevice)
            db.session.add(aPass)
            db.session.commit()
            return json.dumps({'success': True}), 201, {'ContentType': 'application/json'}
        else:
            return json.dumps({'success': False}), 200, {'ContentType': 'application/json'}


# Retrieve all serial numbers (passes) for device
# GET phippsconservatory.xyz/devices/<deviceLibraryIdentifier/registrations/pass.org.conservatory.phipps.membership?passesUpdatedSince=tag
@app.route("/<version>/devices/<deviceLibraryIdentifier>/registrations/<passTypeIdentifier>/", methods=['GET'])
@app.route("/<version>/devices/<deviceLibraryIdentifier>/registrations/<passTypeIdentifier>?passesUpdatedSince=<tag>",
           methods=['GET'])
def get_serial(version, deviceLibraryIdentifier, passTypeIdentifier):
    # Verify that version and pass type ID is correct,
    # that serial number on pass exists, and the
    # authentication token is correct
    # If not, return 401 Unauthorized
    if (version != 'v1') or (passTypeIdentifier != 'pass.org.conservatory.phipps.membership') \
            or (db.session.query(Device).filter((Device.device_lib_id == deviceLibraryIdentifier)).first() is None):
        return not_authorized("Device authorization invalid")
    tag = request.args.get("tag");

    # Look at the registrations table, and determine which passes the device is registered for.
    # Note: Tag is an optional query parameter
    if tag is not None:
        registrations = Device.query.join(registration).join(Card). \
            filter(registration.c.device_id == deviceLibraryIdentifier).filter(Card.last_updated >= tag).all()
    else:
        registrations = Device.query.join(registration).join(Card). \
            filter(registration.c.device_id == deviceLibraryIdentifier).all()

    # Look at the passes table, and determine which passes have changed since the given tag.
    # Don’t include serial numbers of passes that the device didn’t register for.
    # If no update tag is provided, return all the passes that the device is registered for.
    # For example, you return all registered passes the very first time a device communicates with your server.
    if len(registrations) > 0:
        serialNumbers = []
        for aRegistration in registrations:
            serialNumbers.append(aRegistration.pass_id)
        logging.debug("Sending list of passes device is registered for")
        return json.dumps(
            {'lastUpdated': datetime.datetime.now().astimezone(timezone('EST5EDT')), 'serialNumbers': serialNumbers}), \
               200, {'ContentType': 'application/json'}
    else:
        logging.debug("No registrations found! Should at least be one.")
        return not_authorized("No registered devices.")


# Get latest version of a Pass
# GET phippsconservatory.xyz/v1/passes/pass.org.conservatory.phipps.membership/<serialNumber>
@app.route("/<version>/passes/<passTypeIdentifier>/<serialNumber>", methods=['GET'])
def get_latest_version(version, passTypeIdentifier, serialNumber):
    recievedAuth = request.headers.get('Authorization').split(" ")[1]
    if (version != 'v1') or (passTypeIdentifier != 'pass.org.conservatory.phipps.membership'):
        return not_authorized("Version and Pass Type invalid")
    else:
        aPass = Card.query.filter_by(id=serialNumber).first()
        if (aPass is not None and aPass.authenticationToken == recievedAuth):
            return send_from_directory(app.config['PASS_FOLDER'], aPass.file_name,
                                       mimetype='application/vnd.apple.pkpass')


# Unregistering a Device
# DELETE phippsconservatory.xyz/v1/devices/<deviceLibraryIdentifier>/registrations/pass.org.conservatory.phipps.membership/<serialNumber>
@app.route("/<version>/devices/<deviceLibraryIdentifier>/registrations/<passTypeIdentifier>/"
           "<serialNumber>", methods=['DELETE'])
def unregister_device(version, deviceLibraryIdentifier, passTypeIdentifier, serialNumber):
    recievedAuth = request.headers.get('Authorization').split(" ")[1]
    if (version != 'v1') or (passTypeIdentifier != 'pass.org.conservatory.phipps.membership'):
        return not_authorized("Version and Pass Type invalid")
    device = db.session.query(Device).filter((Device.device_lib_id == deviceLibraryIdentifier)).get(1)
    # TODO: Test this
    cards_device = db.session.query(Card, Device).join(registration).filter(
        Device.device_lib_id == deviceLibraryIdentifier)

    # for card, device in cards_device:
    for reg in cards_device.registration:
        db.session.delete(reg)
    db.session.commit()
    return


# Logs errors
# POST phippsconservatory.xyz/v1/log
@app.route("/<version>/log", methods=['POST'])
def logging_error(version):
    msgs = request.values.get('logs')
    if (version != 'v1'):
        return not_authorized("version is invalid")
    for msg in msgs:
        logging.debug(str(msg))
    return json.dumps({'success': True}), 200, {'ContentType': 'application/json'}


# Following is for development ONLY, remove routes and update sidebar for final deployment

# Show all members
# GET phippsconservatory.xyz/members
@app.route("/members", methods=['GET'])
def index_members():
    membership = db.session.query(Member).all()
    return render_template('index_members.html', data=membership)


# Show all passes
# GET phippsconservatory.xyz/members
@app.route("/passes", methods=['GET'])
def index_passes():
    passes = db.session.query(Card).all()
    return render_template('index_passes.html', data=passes)


# Show all devices
# ability to send emails to users
@app.route("/devices", methods=['GET'])
def index_devices():
    devices = db.session.query(Device).all()
    return render_template('index_devices.html', data=devices)


# PRIVATE HELPER FUNCTIONS

# Reading from a provided update.csv file, it will traverse
# record by record of the file, inserting new records or
# updating existing ones
def insertUpdate():
    update_file = os.path.join(app.config['UPLOAD_FOLDER'], "update.csv")
    df = pd.read_csv(update_file)
    df.columns = ["id", "level", "expiration_date", "status", "associates", "last_name", "first_name",
                  "address_1", "address_2", "city", "state", "zip", "email", "notes", "quantity", "quantity_active",
                  "queryid"]
    diff_count = 0
    for row in df.itertuples():
        diff_count += 1
        existing_mem = Member.query.filter_by(id=row.id).first()
        state = False
        exp_date = None
        add_2 = row.address_2
        if row.status == 'Active':
            state = True
        if pd.isna(row.expiration_date) is False:
            exp_date = datetime.strptime(row.expiration_date, '%m/%d/%Y').astimezone(timezone('EST5EDT'))
        if pd.isna(row.address_2):
            add_2 = None
        if existing_mem is None:
            new_member = Member(id=row.id, member_level=row.level,
                                expiration_date=exp_date, status=state,
                                full_name=row.first_name + " " + row.last_name,
                                associated_members=row.associates, address_line_1=row.address_1,
                                address_line_2=add_2,
                                city=row.city, state=row.state, zip=row.zip, email=row.email)
            if exp_date is not None:
                new_pass = Card(authenticationToken=hashlib.sha1(new_member.id.encode('utf-8')).hexdigest(),
                                file_name=row.first_name + row.last_name + ".pkpass",
                                last_sent=None, last_updated=datetime.now().astimezone(timezone('EST5EDT')).strftime("%Y-%m-%dT%H:%M:%S"))
                new_member.cards.append(new_pass)
            db.session.add(new_member)
            db.session.commit()
            if exp_date is not None:
                create_member_pass(row.id, new_pass.file_name)
        else:
            # Update existing member record, create a new pass
            # and then update existing pass record
            existing_mem.member_level = row.level
            existing_mem.expiration_date = exp_date
            existing_mem.status = state
            existing_mem.full_name = row.first_name + " " + row.last_name
            existing_mem.associated_members = row.associates
            existing_mem.address_1 = row.address_1
            existing_mem.address_2 = add_2
            existing_mem.city = row.city
            existing_mem.state = row.state
            existing_mem.zip = row.zip
            existing_mem.email = row.email
            if exp_date is not None:
                create_member_pass(row.id, row.first_name + row.last_name + ".pkpass")
                card = db.session.query(Member, Card).join(member_card_association).join(Card).filter(
                    member_card_association.c.member_id == row.id).first()[1]
                card.last_updated = datetime.now().astimezone(timezone('EST5EDT')).strftime("%Y-%m-%dT%H:%M:%S")
                db.session.commit()
                registrations = Device.query.join(registration).join(Card). \
                    filter(registration.c.card_id == card.id).all()
                # Notify devices that exists
                for device in registrations:
                    logging.debug("Attempting to send push to APN")
                    token = device.push_token
                    alert = {};
                    client = APNSClient(
                        certificate=os.path.join(app.config['CERTIFICATES_FOLDER'], "apn_certificate.pem"),
                        default_error_timeout=10,
                        default_expiration_offset=2592000,
                        default_batch_size=100,
                        default_retries=5)
                    res = client.send(token, alert)
                    logging.debug(res.errors)
                    logging.debug(res.failures)
                    logging.debug(res.message)
                    logging.debug(res.successes)
                    # TODO: if APNs tells you that a push token is invalid,
                    #  remove that device and its registrations from your server.
                    client.close()
                    db.session.commit()
    return diff_count

                    # Checks to make sure file is of csv type


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# Finds differences between two membership csv files,
# deletes the old csv membership file with the new one
# and creates a update.csv file with the difference
def find_difference(newcsv):
    # If no previous membership data is in postGres
    if os.path.isfile(os.path.join(app.config['UPLOAD_FOLDER'], "last_member.csv")) is False:
        os.rename(os.path.join(app.config['UPLOAD_FOLDER'], newcsv),
                  os.path.join(app.config['UPLOAD_FOLDER'], "last_member.csv"))
        shutil.copyfile(os.path.join(app.config['UPLOAD_FOLDER'], "last_member.csv"),
                        os.path.join(app.config['UPLOAD_FOLDER'], "update.csv"))
        return True
    try:
        columns = ["id", "level", "expiration_date", "status", "associates", "last_name", "first_name",
                   "address_1", "address_2", "city", "state", "zip", "email", "notes", "quantity", "quantity_active",
                   "queryid"]

        with open(os.path.join(app.config['UPLOAD_FOLDER'], "last_member.csv"), 'r') as od, open(
                os.path.join(app.config['UPLOAD_FOLDER'], newcsv), 'r') as nd, open(
            os.path.join(app.config['UPLOAD_FOLDER'], "update.csv"), 'w') as diff:
            oldData = set(od)
            writer = csv.writer(diff)
            writer.writerow(columns)
            # diff.write(columns)
            for line in nd:
                if line not in oldData:
                    writer.writerow(line)
            # od.readlines()
            # newData = nd.readlines()
            # writer = csv.writer(outFile)
            # writer.writerow(columns)

        od.close()
        nd.close()
        diff.close()
        if os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], "last_member.csv")):
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], "last_member.csv"))
        os.rename(os.path.join(app.config['UPLOAD_FOLDER'], newcsv),
                  os.path.join(app.config['UPLOAD_FOLDER'], "last_member.csv"))
        return True
    except:
        return False


# Creates or update a card record for a single member record
def create_member_pass(id, filename):
    if os.path.isfile(os.path.join(app.config['PASS_FOLDER'], filename)):
        os.remove(os.path.join(app.config['PASS_FOLDER'], filename))

    member = Member.query.filter_by(id=id).first()
    card = db.session.query(Member, Card).join(member_card_association).join(Card).filter(
        member_card_association.c.member_id == member.id).first()[1]
    cardInfo = Generic()

    # Name, Tier and membership
    cardInfo.addPrimaryField('tier-and-name', member.full_name, member.member_level)
    cardInfo.addSecondaryField('membership-number', member.id, 'Membership Number')

    # Expiration
    if member.expiration_date is not None:
        cardInfo.addSecondaryField('expires', member.expiration_date.strftime("%Y-%m-%d"), 'Expires')
    else:
        cardInfo.addSecondaryField('expires', '', 'Expires')

    # Address, and back fields (including associates)
    fullAddress = member.address_line_1 + ", "
    if member.address_line_2 is not None:
        fullAddress += member.address_line_2 + " "
    fullAddress += member.city + " " + member.state + " " + str(member.zip)
    cardInfo.addAuxiliaryField('address', fullAddress, 'Address Line 1')
    cardInfo.addBackField('associates', member.associated_members, 'Associate Members')
    # if member.additional_child is not None:
    # cardInfo.addBackField('addons', member.additiona_child, 'Add-ons')
    cardInfo.addBackField('operating-hours', 'Saturday - Thursday: 9:30 a.m. - 5 p.m.\nFriday: 9:30 a.m. - 10 p.m.',
                          'Hours')
    cardInfo.addBackField('member-info', '(412)-315-0656\nmembers@phipps.conservatory.org', 'Member Info')
    cardInfo.addBackField('address',
                          'One Schenley Park | Pittsburgh, Pa. 15213\n412/622-6914 | phipps.conservatory.org',
                          'Address')
    # Card properties
    organizationName = 'Phipps Conservatory & Botanical Garden'
    passTypeIdentifier = 'pass.org.conservatory.phipps.membership'
    teamIdentifier = 'M6LYJ8LVCL'
    passfile = Pass(cardInfo, passTypeIdentifier=passTypeIdentifier, organizationName=organizationName,
                    teamIdentifier=teamIdentifier)
    passfile.logoText = 'Phipps Conservatory'
    passfile.description = 'Phipps Conservatory membership pass for {}'.format(member.full_name)
    passfile.serialNumber = str(card.id)
    passfile.barcode = Barcode(message=str(member.id))
    # Value for key 'locations' must be of class NSArray, but is actually of class __NSDictionaryI."
    # Tried to fix manually but too convoluted
    # passfile.locations = Location(latitude=40.4392, longitude=-79.9474)
    passfile.foregroundColor = 'rgb(255, 255, 255)'
    passfile.backgroundColor = 'rgb(121, 161, 56)'
    passfile.labelColor = 'rgb(255, 255, 255)'

    # Icon and Logo needed for pass to be successfully created
    passfile.addFile('icon.png', open('pass utility folder/PhippsSampleGeneric.pass/logo.png', 'rb'))
    passfile.addFile('logo.png', open('pass utility folder/PhippsSampleGeneric.pass/logo.png', 'rb'))
    passfile.webServiceURL = 'https://phippsconservatory.xyz'
    passfile.authenticationToken = str(card.authenticationToken)
    passfile.create(os.path.join(app.config['CERTIFICATES_FOLDER'], "certificate.pem"),
                    os.path.join(app.config['CERTIFICATES_FOLDER'], "key.pem"),
                    os.path.join(app.config['CERTIFICATES_FOLDER'], "wwdr.pem"),
                    os.environ['PEM_PASSWORD'],
                    os.path.join(app.config['PASS_FOLDER'], member.full_name.replace(" ", "") + ".pkpass"))
    return True

# # configure multithreading
# thread = threading.Thread(target=upload_membership, name='TrainingDaemon')
# thread.setDaemon(False)
# thread.start()
