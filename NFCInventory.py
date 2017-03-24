import json
import sys
import time
import datetime

import gspread
import binascii

import Adafruit_PN532 as PN532

from oauth2client.service_account import ServiceAccountCredentials

GDOCS_OAUTH_JSON = 'test-project-6f387c6a3b78.json'

GDOCS_SPREADSHEET_NAME = 'NFC Inventory'

CARD_TYPE_INVALID_STATE = -1
CARD_TYPE_USER = 0
CARD_TYPE_ITEM = 1
CARD_TYPE_UNKNOWN = 2

WORKSHEET_USERIDS_COLUMN_COUNT = 4
WORKSHEET_ITEMIDS_COLUMN_COUNT = 4

def read_nfc_blocking():
    nfchex = None
    while nfchex != None:
        nfchex = pn532.read_passive_target()
    return nfchex

def wait_for_card_removal():
    while pn532.read_passive_target() != None:
        continue
        
def process_card(nfchex):
    hexid = binascii.hexlify(nfchex)
    if UserIDs is None or ItemIDs is None:
        return CARD_TYPE_INVALID_STATE

    try:
        cell = UserIDs.find(str(hexid))
        return CARD_TYPE_USER
    except:
        try:
            ItemIDs.find(str(hexid))
            return CARD_TYPE_ITEM
        except:
            return CARD_TYPE_UNKNOWN
        
def login_open_sheet(oauth_key_file, spreadsheet):
    try:
        scope = ['https://spreadsheets.google.com/feeds']
        credentials = ServiceAccountCredentials.from_json_keyfile_name(oauth_key_file, scope)
        gc = gspread.authorize(credentials)
        print(dir(gc.open(spreadsheet)))
        WorkSheets = gc.open(spreadsheet).worksheets()
        UserIDs = gc.open(spreadsheet).worksheet('UserID')
        ItemIDs = gc.open(spreadsheet).worksheet('ItemID')
        return [UserIDs, ItemIDs]
    except Exception as ex:
        print('Unable to login and get spreadsheet. Check OAuth credentials, spreadsheet name, and make sure spreadsheet is shared to the client_email address in the OAuth .json file!')
        print('Google sheet login failed with error:', ex)
        sys.exit(1)

UserIDs = None
ItemIDs = None

# Configuration for a Raspberry Pi:
CS   = 18
MOSI = 23
MISO = 24
SCLK = 25

pn532 = PN532.PN532(cs=CS, sclk=SCLK, mosi=MOSI, miso=MISO)

pn532.begin()

ic, ver, rev, support = pn532.get_firmware_version()
print('Found PN532 with firmware version: {0}.{1}'.format(ver, rev))

# Configure PN532 to communicate with MiFare cards.
pn532.SAM_configuration()

# Main loop to detect cards and read a block.
print('Waiting for MiFare card...')

while True:
    uid = read_nfc_blocking()
    UserIDRow = -1
    print('Found card with UID: 0x{0}'.format(binascii.hexlify(uid)))
    uidhex = binascii.hexlify(uid)
    print(uidhex)
    if UserIDs is None or ItemIDs is None:
        [UserIDs, ItemIDs] = login_open_sheet(GDOCS_OAUTH_JSON, GDOCS_SPREADSHEET_NAME)
        
    status = process_card(uidhex)
    if status == CARD_TYPE_USER:
        cell = UserIDs.find(str(uidhex))
        print cell
        UserIDRow = cell.row
    elif status == CARD_TYPE_ITEM:
        print('Item Detected. Please scan your ID to begin transaction.')
        continue
    elif status == CARD_TYPE_UNKNOWN:
        addNewCard = raw_input("Do you want to add your card (y/n): ")
        if addNewCard is 'y':
            firstName = raw_input('First Name: ')
            lastName = raw_input('Last Name: ')
            row = UserIDs.row_count
            print(str(row))
            UserIDs.resize(rows=row+1, cols=WORKSHEET_USERIDS_COLUMN_COUNT)
            UserIDs.update_acell('A'+str(row+1), str(uidhex))
            UserIDs.update_acell('B'+str(row+1), str(firstName))
            UserIDs.update_acell('C'+str(row+1), str(lastName))
            #worksheet.append_row([str(uidhex),firstName, lastName])
            UserIDRow = UserIDs.find(str(uidhex)).row
        else:
            print('Scanning for new tag')
                
    print('Please remove your ID.')
    wait_for_card_removal()
    print('Tap ID to finish transaction. Tap item to checkout.')
    
    ScannedItems = []
    itemidhex = None
    
    while itemidhex != uidhex:
        itemid = read_nfc_blocking()
        wait_for_card_removal()
        print('Found ITEM with UID: 0x{0}'.format(binascii.hexlify(itemid)))
        itemidhex = binascii.hexlify(itemid)
        print(itemidhex)
        
        status = process_card(itemidhex)
        if status == CARD_TYPE_USER:
            print('Previously Registered ID found')
        elif status == CARD_TYPE_ITEM:
            ScannedItems.index(itemidhex)
        elif status == CARD_TYPE_UNKNOWN:
            NewItemEntry = raw_input('Item not recognized, would you like to register item? (y/n) ')
            if NewItemEntry == 'y':
                ItemName = raw_input('Item Name: ')
                Description = raw_input('Description: ')
                ItemRow = ItemIDs.row_count
                print(str(ItemRow))
                ItemIDs.resize(rows=ItemRow+1, cols=WORKSHEET_ITEMIDS_COLUMN_COUNT)
                ItemIDs.update_acell('A'+str(ItemRow+1), str(itemidhex))
                ItemIDs.update_acell('B'+str(ItemRow+1), str(ItemName))
                ItemIDs.update_acell('C'+str(ItemRow+1), str(Description))
                ScannedItems.append(itemidhex)
                continue
            else:
                continue
                
    print('User ID Row: '+str(UserIDRow))
    UserIDs.update_acell('D'+str(UserIDRow), str(ScannedItems))
    
    print('Transaction Completed')
    
    # TODO Add a blank row clear function
    print('Waiting 5 seconds')
    time.sleep(5)