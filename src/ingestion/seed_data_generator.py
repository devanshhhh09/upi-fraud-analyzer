import pandas as pd
import json
from src.utils.logger import get_logger
import config

logger = get_logger(__name__)

# Realistic complaint narratives for each UPI fraud type
# Based on actual patterns documented in RBI and CERT-In advisories

SEED_RECORDS = [
    # --- fake_collect_request ---
    {"title": "Lost money via UPI collect request", "description": "I received a UPI collect request of Rs 5000 from an unknown number. The message said it was from my bank for KYC verification. I approved it thinking it was legitimate and the money was instantly debited from my account. Later I found out it was a fraud.", "fraud_type": "fake_collect_request"},
    {"title": "Scammer sent collect request pretending to be buyer", "description": "I listed my old phone on OLX. The buyer said he would pay via UPI and sent me a collect request instead of paying. I mistakenly approved it and Rs 8000 was deducted. He was asking me to approve to receive money but actually it was a payment request.", "fraud_type": "fake_collect_request"},
    {"title": "Fake electricity bill collect request fraud", "description": "Got a UPI collect request saying my electricity connection will be cut if I don't pay immediately. Amount was Rs 1500. I panicked and approved it. Customer care later confirmed no such request was sent by them.", "fraud_type": "fake_collect_request"},
    {"title": "Received collect request from unknown UPI ID", "description": "Someone sent me a collect request on PhonePe saying it was a refund from Flipkart. I accepted thinking I would get money but instead Rs 3000 was deducted. I did not understand that approving collect request means paying money.", "fraud_type": "fake_collect_request"},
    {"title": "Fraud through UPI collect for fake insurance renewal", "description": "A person claiming to be from LIC sent a collect request saying my policy will lapse. The amount was Rs 12000. After I approved it they stopped responding. LIC confirmed no such request was raised.", "fraud_type": "fake_collect_request"},
    {"title": "OLX scammer used collect request trick", "description": "Was selling furniture on OLX. Buyer claimed to be an army officer. Sent a collect request saying this is how army officers pay. Lost Rs 15000 before realizing the mistake.", "fraud_type": "fake_collect_request"},
    {"title": "Fake gas agency collect request", "description": "Received collect request from someone claiming to be Indane Gas. Said I need to pay Rs 700 for subsidy activation. Approved it and lost money. Gas agency denied sending any such request.", "fraud_type": "fake_collect_request"},
    {"title": "Bank KYC collect request scam", "description": "Got a call saying my SBI account will be blocked for KYC. They sent a collect request for Rs 1 saying it is just for verification. After I approved Rs 1 they sent another for Rs 50000. I disconnected immediately.", "fraud_type": "fake_collect_request"},
    {"title": "Collect request fraud during second hand car purchase", "description": "Was buying a used car. Seller sent collect request saying it is advance token money. Lost Rs 20000 and seller disappeared afterwards.", "fraud_type": "fake_collect_request"},
    {"title": "Fake refund collect request from Amazon impersonator", "description": "Someone called claiming to be Amazon and said I have a refund of Rs 2500. They sent a collect request to process the refund. I approved and lost money instead of receiving.", "fraud_type": "fake_collect_request"},

    # --- qr_swap ---
    {"title": "QR code swapped at petrol pump", "description": "Paid at petrol pump by scanning QR code on display board. Later found the QR was a sticker pasted over original. Money went to fraudster account. Station owner was also unaware.", "fraud_type": "qr_swap"},
    {"title": "Fake QR code pasted at temple donation box", "description": "Scanned QR code at temple for donation. QR was fake sticker over original. Rs 500 went to unknown account instead of temple. Temple committee confirmed they did not receive it.", "fraud_type": "qr_swap"},
    {"title": "Restaurant QR replaced by scammer", "description": "Scanned QR at restaurant table to pay bill. Got a call from owner next day saying payment not received. Someone had replaced their QR code sticker with fake one overnight. Lost Rs 1200.", "fraud_type": "qr_swap"},
    {"title": "QR code fraud at parking lot", "description": "Parking lot had QR code on board. Paid Rs 200 by scanning it. Later parking attendant said they never received payment. QR was fake sticker. Attendant had to accept cash payment again.", "fraud_type": "qr_swap"},
    {"title": "Tampered QR at medical shop", "description": "Bought medicines worth Rs 850. Scanned QR to pay. Shop owner said payment not received. QR sticker on counter was fake. Had to pay again by cash.", "fraud_type": "qr_swap"},
    {"title": "OLX seller sent fake QR for product payment", "description": "Seller sent a QR code over WhatsApp claiming it is for receiving payment. I scanned it thinking I need to scan to pay but actually it was a collect QR. Lost Rs 6000.", "fraud_type": "qr_swap"},
    {"title": "Fake QR at railway station booking counter", "description": "Scanned QR near ticket booking area. Paid Rs 340. Got ticket but payment did not go to railway. QR was fake placed by miscreant. Police complaint filed.", "fraud_type": "qr_swap"},
    {"title": "Grocery store QR tampered", "description": "Weekly grocery shopping. Scanned QR at billing counter. Shop owner called saying payment not received. Store staff found fake QR sticker on genuine code. Amount was Rs 2300.", "fraud_type": "qr_swap"},
    {"title": "Fake QR in classifieds ad for flat rent", "description": "Paid token advance for flat via QR code shared on 99acres listing. Owner said he never received. QR belonged to fraudster posing as owner. Lost Rs 25000 advance.", "fraud_type": "qr_swap"},
    {"title": "Swapped QR at vegetable market", "description": "Vegetable vendor had QR on small board. Paid Rs 180. Vendor said amount not received. Someone had placed fake QR sticker on his original code during busy market hours.", "fraud_type": "qr_swap"},

    # --- otp_relay ---
    {"title": "Bank employee impersonator asked for OTP", "description": "Received call from someone claiming to be HDFC Bank. Said my debit card is expiring and needs renewal. Asked for card number and OTP for verification. Shared OTP and Rs 45000 was debited immediately.", "fraud_type": "otp_relay"},
    {"title": "Lost Rs 80000 after sharing OTP with fake RBI officer", "description": "Caller said he was from RBI and my account has been flagged for suspicious activity. To clear my account I need to share OTP. I shared it and all savings were transferred out within minutes.", "fraud_type": "otp_relay"},
    {"title": "OTP fraud during fake prize claim", "description": "Got SMS saying I won KBC lucky draw. Called a number and they said to verify my identity I must share OTP received on my phone. After sharing OTP Rs 15000 was gone from account.", "fraud_type": "otp_relay"},
    {"title": "Shared OTP for fake electricity refund", "description": "Caller said electricity department is giving refund of Rs 900 for overpayment. To process refund they need OTP. Shared OTP. Instead of refund Rs 7500 was debited from account.", "fraud_type": "otp_relay"},
    {"title": "Friend's number used to ask for OTP", "description": "Got WhatsApp message from friend's number asking for OTP urgently saying his phone is not working. Shared OTP. Later found friend's WhatsApp was hacked. Lost Rs 12000 from my account.", "fraud_type": "otp_relay"},
    {"title": "Fake insurance agent collected OTP", "description": "Insurance renewal call. Agent said OTP is needed to update policy records. Shared OTP and premium amount of Rs 18000 was debited but no policy was renewed.", "fraud_type": "otp_relay"},
    {"title": "SIM swap followed by OTP theft", "description": "My SIM stopped working suddenly. Fraudster had done SIM swap at telecom store with fake documents. They received all my OTPs and transferred Rs 2 lakh from bank account.", "fraud_type": "otp_relay"},
    {"title": "OTP asked during fake customer care call", "description": "Called a number I found on Google for Paytm customer care. It was fake number. Executive asked for OTP to verify account. Shared it and wallet balance of Rs 9000 was transferred out.", "fraud_type": "otp_relay"},
    {"title": "Delivery boy asked for OTP to complete delivery", "description": "Fake delivery person called and said OTP is needed to complete my package delivery. Shared OTP. There was no package. OTP was used to authorize a UPI transaction of Rs 3000.", "fraud_type": "otp_relay"},
    {"title": "Shared OTP on fake bank website", "description": "Received SMS with link to update PAN for bank account. Link looked exactly like ICICI website. Entered OTP on the page. Rs 55000 transferred to unknown account within seconds.", "fraud_type": "otp_relay"},

    # --- fake_kyc_freeze ---
    {"title": "Account freeze threat for KYC update", "description": "Got SMS saying my UPI account will be permanently blocked in 24 hours if KYC is not updated. Link was provided. Entered all details including Aadhaar and account number. Account was compromised.", "fraud_type": "fake_kyc_freeze"},
    {"title": "WhatsApp message about KYC expiry fraud", "description": "Received WhatsApp from unknown number with Paytm logo saying KYC expired. Asked to click link and complete video KYC. During process they asked for OTP. Lost Rs 22000.", "fraud_type": "fake_kyc_freeze"},
    {"title": "Fake NPCI KYC message", "description": "SMS claiming to be from NPCI said my UPI ID will be deactivated. Asked to call a number. Executive said he will do remote KYC and asked to install an app. App gave them access to my phone.", "fraud_type": "fake_kyc_freeze"},
    {"title": "Google Pay KYC fraud call", "description": "Caller said my Google Pay KYC is pending and account will be blocked. To keep account active I need to transfer Re 1 to verify account. After Re 1 transfer they asked for Rs 1 lakh for full KYC. Disconnected.", "fraud_type": "fake_kyc_freeze"},
    {"title": "Bank account freeze threat via SMS", "description": "SMS said your SBI YONO account is frozen due to incomplete KYC. Visit link immediately. Link was phishing page. Entered login credentials. Account balance of Rs 35000 was cleared.", "fraud_type": "fake_kyc_freeze"},
    {"title": "PhonePe KYC fraud with screen sharing", "description": "Caller claiming to be PhonePe asked to share screen for KYC verification. Using screen share they saw my UPI PIN being entered and transferred Rs 40000.", "fraud_type": "fake_kyc_freeze"},
    {"title": "Aadhaar KYC fraud for UPI activation", "description": "Fake message said UPI requires fresh Aadhaar KYC by government order. Asked for Aadhaar number and OTP from UIDAI. Used details to open new accounts and take loans.", "fraud_type": "fake_kyc_freeze"},
    {"title": "Urgent KYC update or account blocked message", "description": "Email from fake axis bank address said complete KYC in 2 hours or account blocked. Filled form with all bank details. Next morning Rs 1.2 lakh was gone from account.", "fraud_type": "fake_kyc_freeze"},
    {"title": "Video KYC fraud on WhatsApp", "description": "Call on WhatsApp for video KYC of bank account. They recorded the video call. During call they asked me to show my debit card for verification. Used card details for online transactions.", "fraud_type": "fake_kyc_freeze"},
    {"title": "Fake RBI KYC notification", "description": "Message claimed RBI has made new KYC mandatory. Link sent. Page asked for net banking username password and OTP. Account was drained of Rs 67000 within an hour.", "fraud_type": "fake_kyc_freeze"},

    # --- investment_scam ---
    {"title": "Fake investment app promised 30 percent weekly returns", "description": "Joined a Telegram group that promised high returns on investment through a trading app. Invested Rs 50000 over two months. App showed good profits but when I tried to withdraw nothing came. App disappeared.", "fraud_type": "investment_scam"},
    {"title": "WhatsApp stock tips group turned out to be scam", "description": "Was added to a WhatsApp group by unknown person. Group shared stock tips and showed screenshots of profits. I invested Rs 1 lakh via UPI. Initially got Rs 5000 back to build trust. Then lost everything.", "fraud_type": "investment_scam"},
    {"title": "Crypto investment fraud via UPI", "description": "Online friend showed me a crypto trading platform with guaranteed 40 percent monthly returns. I transferred Rs 2 lakh via UPI to their wallet address. Account got locked after they asked for more money.", "fraud_type": "investment_scam"},
    {"title": "Fake mutual fund agent collected UPI payments", "description": "Person claiming to be SEBI registered agent offered mutual fund with 25 percent annual guaranteed return. Collected Rs 80000 via UPI in installments. Disappeared after collecting money.", "fraud_type": "investment_scam"},
    {"title": "MLM scheme collected money via UPI", "description": "Joined a network marketing scheme that promised Rs 5000 per week. Paid joining fee of Rs 15000 via UPI. Recruited two people as instructed. After two months company shut down website.", "fraud_type": "investment_scam"},
    {"title": "Forex trading scam via Telegram", "description": "Telegram group claimed to have insider forex trading signals with 95 percent accuracy. Paid Rs 30000 for premium signals via UPI. Signals were all wrong. Lost additional Rs 70000 trading.", "fraud_type": "investment_scam"},
    {"title": "Fake IPO allotment fraud", "description": "Received call about guaranteed IPO allotment for upcoming big company. Paid Rs 25000 via UPI as processing fee. IPO came and went. Caller never picked up again.", "fraud_type": "investment_scam"},
    {"title": "YouTube investment scam with fake celebrity endorsement", "description": "Video showed Narendra Modi endorsing an investment app with daily returns of Rs 500. Downloaded app and invested Rs 40000. Initial returns came for one week then app stopped working.", "fraud_type": "investment_scam"},
    {"title": "Agricultural investment fraud collected UPI payments", "description": "Company offered to invest in solar farming and pay quarterly dividends. Paid Rs 1.5 lakh via UPI. Got one dividend of Rs 3000. Company office closed after 3 months.", "fraud_type": "investment_scam"},
    {"title": "Work from home investment scheme fraud", "description": "Job portal asked to pay Rs 5000 via UPI as refundable security deposit for data entry work from home. After payment training material was substandard and they asked for more payment for certification.", "fraud_type": "investment_scam"},

    # --- fake_merchant ---
    {"title": "Fake online store collected UPI payment and disappeared", "description": "Found a website selling branded shoes at 70 percent discount on Instagram ad. Paid Rs 3500 via UPI. Order confirmation received but product never delivered. Website went offline after a week.", "fraud_type": "fake_merchant"},
    {"title": "OLX fake seller fraud for iPhone", "description": "Found iPhone listing on OLX at low price. Seller said he is army officer posted abroad. Asked for advance payment of Rs 15000 via UPI. Paid it. No product. No response.", "fraud_type": "fake_merchant"},
    {"title": "Fake grocery delivery app took payment", "description": "Downloaded grocery delivery app from a link shared on WhatsApp. Placed order of Rs 1800. UPI payment went through. App never showed delivery status. App was fake.", "fraud_type": "fake_merchant"},
    {"title": "Fake medical equipment seller on Facebook", "description": "During COVID bought oximeter from Facebook seller. Paid Rs 2200 via UPI. Received broken non-functional device. Seller blocked after complaint.", "fraud_type": "fake_merchant"},
    {"title": "Fake Swiggy restaurant listing fraud", "description": "Ordered from a new restaurant on Swiggy lookalike app. Paid Rs 650 via UPI. Order never came. App helpline number was switched off. Restaurant did not exist.", "fraud_type": "fake_merchant"},
    {"title": "Fake government store website for khadi products", "description": "Website looked exactly like official Khadi India store. Bought sarees worth Rs 4500. Payment via UPI went through but products never arrived. Website was fake.", "fraud_type": "fake_merchant"},
    {"title": "Airline ticket booking fake site", "description": "Booked flight tickets on website that appeared in Google search. Paid Rs 8700 via UPI. Tickets were never issued. Website disappeared. Real airline had no record of booking.", "fraud_type": "fake_merchant"},
    {"title": "Fake Amazon seller collected advance payment", "description": "WhatsApp message offering products at Amazon warehouse clearance prices. Paid Rs 12000 via UPI to a personal number. No products received. Amazon clarified they have no such scheme.", "fraud_type": "fake_merchant"},
    {"title": "Tuition fee fraud by fake coaching institute", "description": "Online coaching institute collected Rs 18000 fees via UPI for IIT JEE preparation. After payment live classes never started. Website contact details stopped working.", "fraud_type": "fake_merchant"},
    {"title": "Fake Meesho reseller collected payment", "description": "Someone posed as Meesho supplier and offered products at wholesale rates. Paid Rs 7000 via UPI as advance for first order. Products never dispatched. Number blocked.", "fraud_type": "fake_merchant"},

    # --- job_advance_fee ---
    {"title": "Paid Rs 5000 for fake job offer", "description": "Received WhatsApp message saying I am selected for data entry job with Rs 25000 monthly salary. Asked to pay Rs 5000 as security deposit via UPI. After payment they asked for more fees. Realized it was fraud.", "fraud_type": "job_advance_fee"},
    {"title": "Fake HR collected training fee before joining", "description": "Got job offer email for software company. HR asked for Rs 8000 training fee via UPI before joining. Paid it. On joining date office address was wrong and HR unreachable.", "fraud_type": "job_advance_fee"},
    {"title": "Work from home job fraud demanded registration fees", "description": "Instagram ad for work from home job Rs 800 per day. Called number and was told to pay Rs 2500 registration via UPI. After registration task link given did not work and support disappeared.", "fraud_type": "job_advance_fee"},
    {"title": "Placement agency fraud collected multiple fees", "description": "Placement agency promised Gulf job. Collected Rs 45000 in three UPI installments for visa processing and medical fees. After final payment they went silent.", "fraud_type": "job_advance_fee"},
    {"title": "Fake government job notification demanded UPI payment", "description": "Received SMS about railway recruitment. Link led to fake government website. Applied and was told to pay Rs 1500 exam fee via UPI. Paid it. RRB confirmed no such recruitment.", "fraud_type": "job_advance_fee"},
    {"title": "IT company offer letter after paying via UPI", "description": "Naukri profile was accessed by fraudster. Sent fake offer letter from known IT company. Asked for Rs 6000 laptop deposit via UPI. Paid and reported to real company who confirmed fraud.", "fraud_type": "job_advance_fee"},
    {"title": "Fake BPO job asked for ID verification fees", "description": "BPO job offer with good salary. HR said need to pay Rs 1200 for background verification via UPI. After payment was told to wait. Never got joining date.", "fraud_type": "job_advance_fee"},
    {"title": "Nursing job abroad fraud collected visa fees", "description": "Nursing job offer for Singapore hospital. Agency collected Rs 75000 in multiple UPI payments for visa documentation and relocation. Visa never came and agency closed office.", "fraud_type": "job_advance_fee"},
    {"title": "Content writing job demanded software purchase", "description": "Content writing job from home. Rs 3500 via UPI for purchasing licensed content writing software from company. Software was cracked version. Company was fake.", "fraud_type": "job_advance_fee"},
    {"title": "Typing job fraud collected equipment deposit", "description": "Online typing job promised Rs 15000 per month. Asked to pay Rs 4000 equipment refundable deposit via UPI. After payment was given fake tasks with impossible accuracy requirements to avoid paying.", "fraud_type": "job_advance_fee"},

    # --- lottery_reward ---
    {"title": "KBC lottery fraud demanded tax payment via UPI", "description": "Received call saying I won Rs 25 lakh in KBC lucky draw. To claim prize I need to pay Rs 15000 as income tax via UPI. Paid it. They kept asking for more fees. Total loss Rs 45000.", "fraud_type": "lottery_reward"},
    {"title": "Fake Jio recharge prize demanded processing fee", "description": "SMS said my Jio number has won Samsung TV in anniversary lucky draw. To claim need to pay Rs 500 delivery charges via UPI. Paid. Was then asked for Rs 2000 customs fee. Blocked them.", "fraud_type": "lottery_reward"},
    {"title": "International lottery scam collected multiple fees", "description": "Email said I won 50000 British pounds in UK lottery. To transfer winnings need to pay Rs 8000 legal clearance fee via UPI. Paid. They kept asking for more. Total loss Rs 35000.", "fraud_type": "lottery_reward"},
    {"title": "Fake Amazon festive lucky draw winner notification", "description": "SMS said my Amazon order number was selected for Diwali lucky draw and I won iPhone 14. To claim need to pay Rs 200 shipping. Paid via UPI. Phone never came and link expired.", "fraud_type": "lottery_reward"},
    {"title": "Fake cricket match prediction prize", "description": "Telegram group said first 10 correct predictions win cash prize. My prediction matched. To claim Rs 10000 prize need to pay Rs 1500 processing fee via UPI. Paid. Prize never received.", "fraud_type": "lottery_reward"},
    {"title": "Bank anniversary lucky draw fraud", "description": "Call from fake bank said account holder lucky draw winner. Rs 5 lakh prize. To activate prize transfer Re 1 via UPI. After Re 1 transfer they asked for Rs 8000 RBI clearance fee.", "fraud_type": "lottery_reward"},
    {"title": "Fake government scheme reward fraud", "description": "Message claimed PM Kisan Yojana has given bonus reward of Rs 50000 to my aadhaar. To claim need to pay Rs 2000 processing charge via UPI. Paid and lost money. No reward.", "fraud_type": "lottery_reward"},
    {"title": "WhatsApp spinwheel prize fraud", "description": "WhatsApp forward said spin wheel for prizes. I won Rs 50000. Filled details and was asked to pay Rs 999 activation charge via UPI. Paid. Website disappeared.", "fraud_type": "lottery_reward"},
    {"title": "SIM card lucky draw fraud", "description": "Call from telecom company saying my number was randomly selected for Rs 2 lakh cash prize. To receive must pay 5 percent TDS of Rs 10000 via UPI. Disconnected after losing Rs 3000.", "fraud_type": "lottery_reward"},
    {"title": "Fake Paytm cashback prize demand", "description": "Notification showed Rs 5000 cashback prize won on Paytm. But to unlock need to scratch for Rs 100 via UPI. Paid. Then asked for Rs 500 to unlock full amount. Realized scam.", "fraud_type": "lottery_reward"},
]


def generate_seed_dataset() -> pd.DataFrame:
    """Generate a labelled seed dataset from hand-crafted records."""
    df = pd.DataFrame(SEED_RECORDS)
    df["source"] = "seed_dataset"
    df["date_raw"] = "2024-01-01"
    df["url"] = ""

    output_path = config.RAW_DIR / "seed_dataset.json"
    df.to_json(output_path, orient="records", force_ascii=False, indent=2)

    logger.info(f"Seed dataset: {len(df)} records → {output_path}")
    print(f"\nSeed dataset generated: {len(df)} records")
    print(f"\nFraud type distribution:")
    print(df["fraud_type"].value_counts().to_string())
    return df


if __name__ == "__main__":
    generate_seed_dataset()
