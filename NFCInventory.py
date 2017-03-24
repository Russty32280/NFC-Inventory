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
	uid = pn532.read_passive_target()
	UserIDRow = -1

	if uid is None:
		continue

	print('Found card with UID: 0x{0}'.format(binascii.hexlify(uid)))
	uidhex = binascii.hexlify(uid)
	print(uidhex)
	if UserIDs is None or ItemIDs is None:
		[UserIDs, ItemIDs] = login_open_sheet(GDOCS_OAUTH_JSON, GDOCS_SPREADSHEET_NAME)
	try:
		cell = UserIDs.find(str(uidhex))
		print cell
		UserIDRow = cell.row
	except:
		try:
			ItemIDs.find(str(uidhex))
			print('Item Detected. Please scan ID to begin transaction')
	                while pn532.read_passive_target() != None:
	                        continue

			continue
		except:
			addNewCard = raw_input("Do you want to add your card (y/n): ")
			if addNewCard is 'y':
				firstName = raw_input('First Name: ')
				lastName = raw_input('Last Name: ')
				row = UserIDs.row_count
				print(str(row))
				UserIDs.resize(rows=row+1, cols=4)
				UserIDs.update_acell('A'+str(row+1), str(uidhex))
				UserIDs.update_acell('B'+str(row+1), str(firstName))
				UserIDs.update_acell('C'+str(row+1), str(lastName))
				#worksheet.append_row([str(uidhex),firstName, lastName])
				UserIDRow = UserIDs.find(str(uidhex)).row
				
			else:
				print('Scanning for new tag')
			"""
			print('Error, logging in again')
			UserIDs = None
			time.sleep(5)
			continue
			"""

	raw_input('Remove ID. Presss enter to start checkout.')
	print('Tap ID to finish transaction')

	ScannedItems = []

	itemidhex = None

	while itemidhex != uidhex:
		itemid = None
		while itemid == None:
			itemid = pn532.read_passive_target()

		while pn532.read_passive_target() != None:
			continue


#	        	if itemid is None:
#                		continue		

	        print('Found ITEM with UID: 0x{0}'.format(binascii.hexlify(itemid)))
        	itemidhex = binascii.hexlify(itemid)
        	print(itemidhex)
		
		try:
			ScannedItems.index(itemidhex)
			continue
		except:
				
	        	try:
        	        	ItemCell = ItemIDs.find(str(itemidhex))
                		print ItemCell
				ScannedItems.append(itemidhex)
	
			except:
				try:
					UserIDs.find(str(itemidhex))
					print('Previously Registered ID found')
				except:

					NewItemEntry = raw_input('Item not recognized, would you like to register item? (y/n) ')
					if NewItemEntry == 'y':
						ItemName = raw_input('Item Name: ')
                       				Description = raw_input('Description: ')
	               	 		        ItemRow = ItemIDs.row_count
                       				print(str(ItemRow))
                       				ItemIDs.resize(rows=ItemRow+1, cols=3)
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
