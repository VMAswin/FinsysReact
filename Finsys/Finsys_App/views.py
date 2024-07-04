#React Finsys

from django.shortcuts import render
from Finsys_App.models import *
from django.http import HttpResponse, JsonResponse
from .serializers import *
from django.contrib import auth
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
import json
from rest_framework.decorators import api_view, parser_classes
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.conf import settings
import random
import string
from datetime import date
from datetime import timedelta
from django.db.models import Q
from django.template.loader import get_template
from xhtml2pdf import pisa
from django.core.mail import send_mail, EmailMessage
from io import BytesIO
from django.conf import settings
from datetime import datetime
from copy import deepcopy
# Create your views here.


def home(request):
    return HttpResponse("Okay")


@api_view(("POST",))
def Fin_companyReg_action(request):
    if request.method == "POST":
        if Fin_Login_Details.objects.filter(
            User_name=request.data["User_name"]
        ).exists():
            return Response(
                {
                    "status": False,
                    "message": "This username already exists. Sign up again",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        elif Fin_Company_Details.objects.filter(Email=request.data["Email"]).exists():
            return Response(
                {
                    "status": False,
                    "message": "This email already exists. Sign up again",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        else:
            request.data["User_Type"] = "Company"

            serializer = LoginDetailsSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                loginId = Fin_Login_Details.objects.get(id=serializer.data["id"]).id

                code_length = 8
                characters = string.ascii_letters + string.digits  # Letters and numbers

                while True:
                    unique_code = "".join(
                        random.choice(characters) for _ in range(code_length)
                    )
                    # Check if the code already exists in the table
                    if not Fin_Company_Details.objects.filter(
                        Company_Code=unique_code
                    ).exists():
                        break

                request.data["Login_Id"] = loginId
                request.data["Company_Code"] = unique_code
                request.data["Admin_approval_status"] = "NULL"
                request.data["Distributor_approval_status"] = "NULL"
                companySerializer = CompanyDetailsSerializer(data=request.data)
                if companySerializer.is_valid():
                    companySerializer.save()
                    return Response(
                        {"status": True, "data": companySerializer.data},
                        status=status.HTTP_201_CREATED,
                    )
                else:
                    return Response(
                        {"status": False, "data": companySerializer.errors},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
            else:
                return Response(
                    {"status": False, "data": serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST,
                )


@api_view(("PUT",))
@parser_classes((MultiPartParser, FormParser))
def Fin_CompanyReg2_action2(request):
    try:
        login_id = request.data["Id"]
        data = Fin_Login_Details.objects.get(id=login_id)
        com = Fin_Company_Details.objects.get(Login_Id=data.id)

        dis_code = request.data.get("distId", "")
        print(dis_code)
        distr_id = None
        if dis_code:
            if not Fin_Distributors_Details.objects.filter(
                Distributor_Code=dis_code
            ).exists():
                return Response(
                    {
                        "status": False,
                        "message": "Sorry, distributor id does not exist",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            else:
                distr_id = Fin_Distributors_Details.objects.get(
                    Distributor_Code=dis_code
                )
                # request.data["Distributor_id"] = Fin_Distributors_Details.objects.filter(Distributor_Code=dis_code).first().id
                # print('distrId==',request.data['Distributor_id'])
        serializer = CompanyDetailsSerializer(com, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()

            # Update the company with trial period dates
            com.Start_Date = date.today()
            com.End_date = date.today() + timedelta(days=30)
            com.Distributor_id = distr_id
            com.save()

            # Create a trial period instance
            trial_period = TrialPeriod(
                company=com, start_date=com.Start_Date, end_date=com.End_date
            )
            trial_period.save()

            return Response(
                {"status": True, "data": serializer.data}, status=status.HTTP_200_OK
            )
        else:
            return Response(
                {"status": False, "data": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

    except Fin_Login_Details.DoesNotExist:
        return Response(
            {"status": False, "message": "Login details not found"},
            status=status.HTTP_404_NOT_FOUND,
        )
    except Fin_Company_Details.DoesNotExist:
        return Response(
            {"status": False, "message": "Company details not found"},
            status=status.HTTP_404_NOT_FOUND,
        )
    except Exception as e:
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(("POST",))
def Fin_Add_Modules(request):
    try:
        login_id = request.data["Login_Id"]
        data = Fin_Login_Details.objects.get(id=login_id)
        com = Fin_Company_Details.objects.get(Login_Id=data.id)

        request.data["company_id"] = com.id

        serializer = ModulesListSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()

            # Adding Default Units under company
            Fin_Units.objects.create(Company=com, name="BOX")
            Fin_Units.objects.create(Company=com, name="NUMBER")
            Fin_Units.objects.create(Company=com, name="PACK")

            # Adding Default loan terms under company by TINTO MT
            Fin_Loan_Term.objects.create(company=com, duration=3, term="MONTH", days=90)
            Fin_Loan_Term.objects.create(
                company=com, duration="6", term="MONTH", days=180
            )
            Fin_Loan_Term.objects.create(company=com, duration=1, term="YEAR", days=365)

            # Adding default accounts for companies

            created_date = date.today()
            account_info = [
                {
                    "company_id": com,
                    "Login_Id": data,
                    "account_type": "Accounts Payable",
                    "account_name": "Accounts Payable",
                    "credit_card_no": "",
                    "sub_account": "",
                    "parent_account": "",
                    "bank_account_no": None,
                    "account_code": "",
                    "description": "This is an account of all the money which you owe to others like a pending bill payment to a vendor,etc.",
                    "balance": 0.0,
                    "balance_type": "",
                    "date": created_date,
                    "create_status": "default",
                    "status": "active",
                },
                {
                    "company_id": com,
                    "Login_Id": data,
                    "account_type": "Accounts Receivable",
                    "account_name": "Accounts Receivable",
                    "credit_card_no": "",
                    "sub_account": "",
                    "parent_account": "",
                    "bank_account_no": None,
                    "account_code": "",
                    "description": "The money that customers owe you becomes the accounts receivable. A good example of this is a payment expected from an invoice sent to your customer.",
                    "balance": 0.0,
                    "balance_type": "",
                    "date": created_date,
                    "create_status": "default",
                    "status": "active",
                },
                {
                    "company_id": com,
                    "Login_Id": data,
                    "account_type": "Other Current Asset",
                    "account_name": "Advance Tax",
                    "credit_card_no": "",
                    "sub_account": "",
                    "parent_account": "",
                    "bank_account_no": None,
                    "account_code": "",
                    "description": "Any tax which is paid in advance is recorded into the advance tax account. This advance tax payment could be a quarterly, half yearly or yearly payment",
                    "balance": 0.0,
                    "balance_type": "",
                    "date": created_date,
                    "create_status": "default",
                    "status": "active",
                },
                {
                    "company_id": com,
                    "Login_Id": data,
                    "account_type": "Expense",
                    "account_name": "Advertising and Marketing",
                    "credit_card_no": "",
                    "sub_account": "",
                    "parent_account": "",
                    "bank_account_no": None,
                    "account_code": "",
                    "description": "Your expenses on promotional, marketing and advertising activities like banners, web-adds, trade shows, etc. are recorded in advertising and marketing account.",
                    "balance": 0.0,
                    "balance_type": "",
                    "date": created_date,
                    "create_status": "default",
                    "status": "active",
                },
                {
                    "company_id": com,
                    "Login_Id": data,
                    "account_type": "Expense",
                    "account_name": "Automobile Expense",
                    "credit_card_no": "",
                    "sub_account": "",
                    "parent_account": "",
                    "bank_account_no": None,
                    "account_code": "",
                    "description": "Transportation related expenses like fuel charges and maintenance charges for automobiles, are included to the automobile expense account.",
                    "balance": 0.0,
                    "balance_type": "",
                    "date": created_date,
                    "create_status": "default",
                    "status": "active",
                },
                {
                    "company_id": com,
                    "Login_Id": data,
                    "account_type": "Expense",
                    "account_name": "Bad Debt",
                    "credit_card_no": "",
                    "sub_account": "",
                    "parent_account": "",
                    "bank_account_no": None,
                    "account_code": "",
                    "description": "Any amount which is lost and is unrecoverable is recorded into the bad debt account.",
                    "balance": 0.0,
                    "balance_type": "",
                    "date": created_date,
                    "create_status": "default",
                    "status": "active",
                },
                {
                    "company_id": com,
                    "Login_Id": data,
                    "account_type": "Expense",
                    "account_name": "Bank Fees and Charges",
                    "credit_card_no": "",
                    "sub_account": "",
                    "parent_account": "",
                    "bank_account_no": None,
                    "account_code": "",
                    "description": " Any bank fees levied is recorded into the bank fees and charges account. A bank account maintenance fee, transaction charges, a late payment fee are some examples.",
                    "balance": 0.0,
                    "balance_type": "",
                    "date": created_date,
                    "create_status": "default",
                    "status": "active",
                },
                {
                    "company_id": com,
                    "Login_Id": data,
                    "account_type": "Expense",
                    "account_name": "Consultant Expense",
                    "credit_card_no": "",
                    "sub_account": "",
                    "parent_account": "",
                    "bank_account_no": None,
                    "account_code": "",
                    "description": "Charges for availing the services of a consultant is recorded as a consultant expenses. The fees paid to a soft skills consultant to impart personality development training for your employees is a good example.",
                    "balance": 0.0,
                    "balance_type": "",
                    "date": created_date,
                    "create_status": "default",
                    "status": "active",
                },
                {
                    "company_id": com,
                    "Login_Id": data,
                    "account_type": "Cost Of Goods Sold",
                    "account_name": "Cost of Goods Sold",
                    "credit_card_no": "",
                    "sub_account": "",
                    "parent_account": "",
                    "bank_account_no": None,
                    "account_code": "",
                    "description": "An expense account which tracks the value of the goods sold.",
                    "balance": 0.0,
                    "balance_type": "",
                    "date": created_date,
                    "create_status": "default",
                    "status": "active",
                },
                {
                    "company_id": com,
                    "Login_Id": data,
                    "account_type": "Expense",
                    "account_name": "Credit Card Charges",
                    "credit_card_no": "",
                    "sub_account": "",
                    "parent_account": "",
                    "bank_account_no": None,
                    "account_code": "",
                    "description": " Service fees for transactions , balance transfer fees, annual credit fees and other charges levied on a credit card are recorded into the credit card account.",
                    "balance": 0.0,
                    "balance_type": "",
                    "date": created_date,
                    "create_status": "default",
                    "status": "active",
                },
                {
                    "company_id": com,
                    "Login_Id": data,
                    "account_type": "Expense",
                    "account_name": "Depreciation Expense",
                    "credit_card_no": "",
                    "sub_account": "",
                    "parent_account": "",
                    "bank_account_no": None,
                    "account_code": "",
                    "description": "Any depreciation in value of your assets can be captured as a depreciation expense.",
                    "balance": 0.0,
                    "balance_type": "",
                    "date": created_date,
                    "create_status": "default",
                    "status": "active",
                },
                {
                    "company_id": com,
                    "Login_Id": data,
                    "account_type": "Income",
                    "account_name": "Discount",
                    "credit_card_no": "",
                    "sub_account": "",
                    "parent_account": "",
                    "bank_account_no": None,
                    "account_code": "",
                    "description": "Any reduction on your selling price as a discount can be recorded into the discount account.",
                    "balance": 0.0,
                    "balance_type": "",
                    "date": created_date,
                    "create_status": "default",
                    "status": "active",
                },
                {
                    "company_id": com,
                    "Login_Id": data,
                    "account_type": "Equity",
                    "account_name": "Drawings",
                    "credit_card_no": "",
                    "sub_account": "",
                    "parent_account": "",
                    "bank_account_no": None,
                    "account_code": "",
                    "description": "The money withdrawn from a business by its owner can be tracked with this account.",
                    "balance": 0.0,
                    "balance_type": "",
                    "date": created_date,
                    "create_status": "default",
                    "status": "active",
                },
                {
                    "company_id": com,
                    "Login_Id": data,
                    "account_type": "Other Current Asset",
                    "account_name": "Employee Advance",
                    "credit_card_no": "",
                    "sub_account": "",
                    "parent_account": "",
                    "bank_account_no": None,
                    "account_code": "",
                    "description": "Money paid out to an employee in advance can be tracked here till it's repaid or shown to be spent for company purposes",
                    "balance": 0.0,
                    "balance_type": "",
                    "date": created_date,
                    "create_status": "default",
                    "status": "active",
                },
                {
                    "company_id": com,
                    "Login_Id": data,
                    "account_type": "Other Current Liability",
                    "account_name": "Employee Reimbursements",
                    "credit_card_no": "",
                    "sub_account": "",
                    "parent_account": "",
                    "bank_account_no": None,
                    "account_code": "",
                    "description": "This account can be used to track the reimbursements that are due to be paid out to employees.",
                    "balance": 0.0,
                    "balance_type": "",
                    "date": created_date,
                    "create_status": "default",
                    "status": "active",
                },
                {
                    "company_id": com,
                    "Login_Id": data,
                    "account_type": "Other Expense",
                    "account_name": "Exchange Gain or Loss",
                    "credit_card_no": "",
                    "sub_account": "",
                    "parent_account": "",
                    "bank_account_no": None,
                    "account_code": "",
                    "description": "Changing the conversion rate can result in a gain or a loss. You can record this into the exchange gain or loss account.",
                    "balance": 0.0,
                    "balance_type": "",
                    "date": created_date,
                    "create_status": "default",
                    "status": "active",
                },
                {
                    "company_id": com,
                    "Login_Id": data,
                    "account_type": "Fixed Asset",
                    "account_name": "Furniture and Equipment",
                    "credit_card_no": "",
                    "sub_account": "",
                    "parent_account": "",
                    "bank_account_no": None,
                    "account_code": "",
                    "description": "Purchases of furniture and equipment for your office that can be used for a long period of time usually exceeding one year can be tracked with this account.",
                    "balance": 0.0,
                    "balance_type": "",
                    "date": created_date,
                    "create_status": "default",
                    "status": "active",
                },
                {
                    "company_id": com,
                    "Login_Id": data,
                    "account_type": "Income",
                    "account_name": "General Income",
                    "credit_card_no": "",
                    "sub_account": "",
                    "parent_account": "",
                    "bank_account_no": None,
                    "account_code": "",
                    "description": "A general category of account where you can record any income which cannot be recorded into any other category",
                    "balance": 0.0,
                    "balance_type": "",
                    "date": created_date,
                    "create_status": "default",
                    "status": "active",
                },
                {
                    "company_id": com,
                    "Login_Id": data,
                    "account_type": "Income",
                    "account_name": "Interest Income",
                    "credit_card_no": "",
                    "sub_account": "",
                    "parent_account": "",
                    "bank_account_no": None,
                    "account_code": "",
                    "description": "A percentage of your balances and deposits are given as interest to you by your banks and financial institutions. This interest is recorded into the interest income account.",
                    "balance": 0.0,
                    "balance_type": "",
                    "date": created_date,
                    "create_status": "default",
                    "status": "active",
                },
                {
                    "company_id": com,
                    "Login_Id": data,
                    "account_type": "Stock",
                    "account_name": "Inventory Asset",
                    "credit_card_no": "",
                    "sub_account": "",
                    "parent_account": "",
                    "bank_account_no": None,
                    "account_code": "",
                    "description": "An account which tracks the value of goods in your inventory.",
                    "balance": 0.0,
                    "balance_type": "",
                    "date": created_date,
                    "create_status": "default",
                    "status": "active",
                },
                {
                    "company_id": com,
                    "Login_Id": data,
                    "account_type": "Expense",
                    "account_name": "IT and Internet Expenses",
                    "credit_card_no": "",
                    "sub_account": "",
                    "parent_account": "",
                    "bank_account_no": None,
                    "account_code": "",
                    "description": "Money spent on your IT infrastructure and usage like internet connection, purchasing computer equipment etc is recorded as an IT and Computer Expense",
                    "balance": 0.0,
                    "balance_type": "",
                    "date": created_date,
                    "create_status": "default",
                    "status": "active",
                },
                {
                    "company_id": com,
                    "Login_Id": data,
                    "account_type": "Expense",
                    "account_name": "Janitorial Expense",
                    "credit_card_no": "",
                    "sub_account": "",
                    "parent_account": "",
                    "bank_account_no": None,
                    "account_code": "",
                    "description": "All your janitorial and cleaning expenses are recorded into the janitorial expenses account.",
                    "balance": 0.0,
                    "balance_type": "",
                    "date": created_date,
                    "create_status": "default",
                    "status": "active",
                },
                {
                    "company_id": com,
                    "Login_Id": data,
                    "account_type": "Income",
                    "account_name": "Late Fee Income",
                    "credit_card_no": "",
                    "sub_account": "",
                    "parent_account": "",
                    "bank_account_no": None,
                    "account_code": "",
                    "description": "Any late fee income is recorded into the late fee income account. The late fee is levied when the payment for an invoice is not received by the due date",
                    "balance": 0.0,
                    "balance_type": "",
                    "date": created_date,
                    "create_status": "default",
                    "status": "active",
                },
                {
                    "company_id": com,
                    "Login_Id": data,
                    "account_type": "Expense",
                    "account_name": "Lodging",
                    "credit_card_no": "",
                    "sub_account": "",
                    "parent_account": "",
                    "bank_account_no": None,
                    "account_code": "",
                    "description": "Any expense related to putting up at motels etc while on business travel can be entered here.",
                    "balance": 0.0,
                    "balance_type": "",
                    "date": created_date,
                    "create_status": "default",
                    "status": "active",
                },
                {
                    "company_id": com,
                    "Login_Id": data,
                    "account_type": "Expense",
                    "account_name": "Meals and Entertainment",
                    "credit_card_no": "",
                    "sub_account": "",
                    "parent_account": "",
                    "bank_account_no": None,
                    "account_code": "",
                    "description": "Expenses on food and entertainment are recorded into this account.",
                    "balance": 0.0,
                    "balance_type": "",
                    "date": created_date,
                    "create_status": "default",
                    "status": "active",
                },
                {
                    "company_id": com,
                    "Login_Id": data,
                    "account_type": "Expense",
                    "account_name": "Office Supplies",
                    "credit_card_no": "",
                    "sub_account": "",
                    "parent_account": "",
                    "bank_account_no": None,
                    "account_code": "",
                    "description": "All expenses on purchasing office supplies like stationery are recorded into the office supplies account.",
                    "balance": 0.0,
                    "balance_type": "",
                    "date": created_date,
                    "create_status": "default",
                    "status": "active",
                },
                {
                    "company_id": com,
                    "Login_Id": data,
                    "account_type": "Other Current Liability",
                    "account_name": "Opening Balance Adjustments",
                    "credit_card_no": "",
                    "sub_account": "",
                    "parent_account": "",
                    "bank_account_no": None,
                    "account_code": "",
                    "description": "This account will hold the difference in the debits and credits entered during the opening balance.",
                    "balance": 0.0,
                    "balance_type": "",
                    "date": created_date,
                    "create_status": "default",
                    "status": "active",
                },
                {
                    "company_id": com,
                    "Login_Id": data,
                    "account_type": "Equity",
                    "account_name": "Opening Balance Offset",
                    "credit_card_no": "",
                    "sub_account": "",
                    "parent_account": "",
                    "bank_account_no": None,
                    "account_code": "",
                    "description": "This is an account where you can record the balance from your previous years earning or the amount set aside for some activities. It is like a buffer account for your funds.",
                    "balance": 0.0,
                    "balance_type": "",
                    "date": created_date,
                    "create_status": "default",
                    "status": "active",
                },
                {
                    "company_id": com,
                    "Login_Id": data,
                    "account_type": "Income",
                    "account_name": "Other Charges",
                    "credit_card_no": "",
                    "sub_account": "",
                    "parent_account": "",
                    "bank_account_no": None,
                    "account_code": "",
                    "description": "Miscellaneous charges like adjustments made to the invoice can be recorded in this account.",
                    "balance": 0.0,
                    "balance_type": "",
                    "date": created_date,
                    "create_status": "default",
                    "status": "active",
                },
                {
                    "company_id": com,
                    "Login_Id": data,
                    "account_type": "Expense",
                    "account_name": "Other Expenses",
                    "credit_card_no": "",
                    "sub_account": "",
                    "parent_account": "",
                    "bank_account_no": None,
                    "account_code": "",
                    "description": " Any minor expense on activities unrelated to primary business operations is recorded under the other expense account.",
                    "balance": 0.0,
                    "balance_type": "",
                    "date": created_date,
                    "create_status": "default",
                    "status": "active",
                },
                {
                    "company_id": com,
                    "Login_Id": data,
                    "account_type": "Equity",
                    "account_name": "Owner's Equity",
                    "credit_card_no": "",
                    "sub_account": "",
                    "parent_account": "",
                    "bank_account_no": None,
                    "account_code": "",
                    "description": "The owners rights to the assets of a company can be quantified in the owner's equity account.",
                    "balance": 0.0,
                    "balance_type": "",
                    "date": created_date,
                    "create_status": "default",
                    "status": "active",
                },
                {
                    "company_id": com,
                    "Login_Id": data,
                    "account_type": "Cash",
                    "account_name": "Petty Cash",
                    "credit_card_no": "",
                    "sub_account": "",
                    "parent_account": "",
                    "bank_account_no": None,
                    "account_code": "",
                    "description": "It is a small amount of cash that is used to pay your minor or casual expenses rather than writing a check.",
                    "balance": 0.0,
                    "balance_type": "",
                    "date": created_date,
                    "create_status": "default",
                    "status": "active",
                },
                {
                    "company_id": com,
                    "Login_Id": data,
                    "account_type": "Expense",
                    "account_name": "Postage",
                    "credit_card_no": "",
                    "sub_account": "",
                    "parent_account": "",
                    "bank_account_no": None,
                    "account_code": "",
                    "description": "Your expenses on ground mails, shipping and air mails can be recorded under the postage account.",
                    "balance": 0.0,
                    "balance_type": "",
                    "date": created_date,
                    "create_status": "default",
                    "status": "active",
                },
                {
                    "company_id": com,
                    "Login_Id": data,
                    "account_type": "Other Current Asset",
                    "account_name": "Prepaid Expenses",
                    "credit_card_no": "",
                    "sub_account": "",
                    "parent_account": "",
                    "bank_account_no": None,
                    "account_code": "",
                    "description": "An asset account that reports amounts paid in advance while purchasing goods or services from a vendor.",
                    "balance": 0.0,
                    "balance_type": "",
                    "date": created_date,
                    "create_status": "default",
                    "status": "active",
                },
                {
                    "company_id": com,
                    "Login_Id": data,
                    "account_type": "Expense",
                    "account_name": "Printing and Stationery",
                    "credit_card_no": "",
                    "sub_account": "",
                    "parent_account": "",
                    "bank_account_no": None,
                    "account_code": "",
                    "description": " Expenses incurred by the organization towards printing and stationery.",
                    "balance": 0.0,
                    "balance_type": "",
                    "date": created_date,
                    "create_status": "default",
                    "status": "active",
                },
                {
                    "company_id": com,
                    "Login_Id": data,
                    "account_type": "Expense",
                    "account_name": "Rent Expense",
                    "credit_card_no": "",
                    "sub_account": "",
                    "parent_account": "",
                    "bank_account_no": None,
                    "account_code": "",
                    "description": "The rent paid for your office or any space related to your business can be recorded as a rental expense.",
                    "balance": 0.0,
                    "balance_type": "",
                    "date": created_date,
                    "create_status": "default",
                    "status": "active",
                },
                {
                    "company_id": com,
                    "Login_Id": data,
                    "account_type": "Expense",
                    "account_name": "Repairs and Maintenance",
                    "credit_card_no": "",
                    "sub_account": "",
                    "parent_account": "",
                    "bank_account_no": None,
                    "account_code": "",
                    "description": "The costs involved in maintenance and repair of assets is recorded under this account.",
                    "balance": 0.0,
                    "balance_type": "",
                    "date": created_date,
                    "create_status": "default",
                    "status": "active",
                },
                {
                    "company_id": com,
                    "Login_Id": data,
                    "account_type": "Equity",
                    "account_name": "Retained Earnings",
                    "credit_card_no": "",
                    "sub_account": "",
                    "parent_account": "",
                    "bank_account_no": None,
                    "account_code": "",
                    "description": "The earnings of your company which are not distributed among the share holders is accounted as retained earnings.",
                    "balance": 0.0,
                    "balance_type": "",
                    "date": created_date,
                    "create_status": "default",
                    "status": "active",
                },
                {
                    "company_id": com,
                    "Login_Id": data,
                    "account_type": "Expense",
                    "account_name": "Salaries and Employee Wages",
                    "credit_card_no": "",
                    "sub_account": "",
                    "parent_account": "",
                    "bank_account_no": None,
                    "account_code": "",
                    "description": "Salaries for your employees and the wages paid to workers are recorded under the salaries and wages account.",
                    "balance": 0.0,
                    "balance_type": "",
                    "date": created_date,
                    "create_status": "default",
                    "status": "active",
                },
                {
                    "company_id": com,
                    "Login_Id": data,
                    "account_type": "Income",
                    "account_name": "Sales",
                    "credit_card_no": "",
                    "sub_account": "",
                    "parent_account": "",
                    "bank_account_no": None,
                    "account_code": "",
                    "description": " The income from the sales in your business is recorded under the sales account.",
                    "balance": 0.0,
                    "balance_type": "",
                    "date": created_date,
                    "create_status": "default",
                    "status": "active",
                },
                {
                    "company_id": com,
                    "Login_Id": data,
                    "account_type": "Income",
                    "account_name": "Shipping Charge",
                    "credit_card_no": "",
                    "sub_account": "",
                    "parent_account": "",
                    "bank_account_no": None,
                    "account_code": "",
                    "description": "Shipping charges made to the invoice will be recorded in this account.",
                    "balance": 0.0,
                    "balance_type": "",
                    "date": created_date,
                    "create_status": "default",
                    "status": "active",
                },
                {
                    "company_id": com,
                    "Login_Id": data,
                    "account_type": "Other Liability",
                    "account_name": "Tag Adjustments",
                    "credit_card_no": "",
                    "sub_account": "",
                    "parent_account": "",
                    "bank_account_no": None,
                    "account_code": "",
                    "description": " This adjustment account tracks the transfers between different reporting tags.",
                    "balance": 0.0,
                    "balance_type": "",
                    "date": created_date,
                    "create_status": "default",
                    "status": "active",
                },
                {
                    "company_id": com,
                    "Login_Id": data,
                    "account_type": "Other Current Liability",
                    "account_name": "Tax Payable",
                    "credit_card_no": "",
                    "sub_account": "",
                    "parent_account": "",
                    "bank_account_no": None,
                    "account_code": "",
                    "description": "The amount of money which you owe to your tax authority is recorded under the tax payable account. This amount is a sum of your outstanding in taxes and the tax charged on sales.",
                    "balance": 0.0,
                    "balance_type": "",
                    "date": created_date,
                    "create_status": "default",
                    "status": "active",
                },
                {
                    "company_id": com,
                    "Login_Id": data,
                    "account_type": "Expense",
                    "account_name": "Telephone Expense",
                    "credit_card_no": "",
                    "sub_account": "",
                    "parent_account": "",
                    "bank_account_no": None,
                    "account_code": "",
                    "description": "The expenses on your telephone, mobile and fax usage are accounted as telephone expenses.",
                    "balance": 0.0,
                    "balance_type": "",
                    "date": created_date,
                    "create_status": "default",
                    "status": "active",
                },
                {
                    "company_id": com,
                    "Login_Id": data,
                    "account_type": "Expense",
                    "account_name": "Travel Expense",
                    "credit_card_no": "",
                    "sub_account": "",
                    "parent_account": "",
                    "bank_account_no": None,
                    "account_code": "",
                    "description": " Expenses on business travels like hotel bookings, flight charges, etc. are recorded as travel expenses.",
                    "balance": 0.0,
                    "balance_type": "",
                    "date": created_date,
                    "create_status": "default",
                    "status": "active",
                },
                {
                    "company_id": com,
                    "Login_Id": data,
                    "account_type": "Expense",
                    "account_name": "Uncategorized",
                    "credit_card_no": "",
                    "sub_account": "",
                    "parent_account": "",
                    "bank_account_no": None,
                    "account_code": "",
                    "description": "This account can be used to temporarily track expenses that are yet to be identified and classified into a particular category.",
                    "balance": 0.0,
                    "balance_type": "",
                    "date": created_date,
                    "create_status": "default",
                    "status": "active",
                },
                {
                    "company_id": com,
                    "Login_Id": data,
                    "account_type": "Cash",
                    "account_name": "Undeposited Funds",
                    "credit_card_no": "",
                    "sub_account": "",
                    "parent_account": "",
                    "bank_account_no": None,
                    "account_code": "",
                    "description": "Record funds received by your company yet to be deposited in a bank as undeposited funds and group them as a current asset in your balance sheet.",
                    "balance": 0.0,
                    "balance_type": "",
                    "date": created_date,
                    "create_status": "default",
                    "status": "active",
                },
                {
                    "company_id": com,
                    "Login_Id": data,
                    "account_type": "Other Current Liability",
                    "account_name": "Unearned Revenue",
                    "credit_card_no": "",
                    "sub_account": "",
                    "parent_account": "",
                    "bank_account_no": None,
                    "account_code": "",
                    "description": "A liability account that reports amounts received in advance of providing goods or services. When the goods or services are provided, this account balance is decreased and a revenue account is increased.",
                    "balance": 0.0,
                    "balance_type": "",
                    "date": created_date,
                    "create_status": "default",
                    "status": "active",
                },
                {
                    "company_id": com,
                    "Login_Id": data,
                    "account_type": "Equity",
                    "account_name": "Capital Stock",
                    "credit_card_no": "",
                    "sub_account": "",
                    "parent_account": "",
                    "bank_account_no": None,
                    "account_code": "",
                    "description": " An equity account that tracks the capital introduced when a business is operated through a company or corporation.",
                    "balance": 0.0,
                    "balance_type": "",
                    "date": created_date,
                    "create_status": "default",
                    "status": "active",
                },
                {
                    "company_id": com,
                    "Login_Id": data,
                    "account_type": "Long Term Liability",
                    "account_name": "Construction Loans",
                    "credit_card_no": "",
                    "sub_account": "",
                    "parent_account": "",
                    "bank_account_no": None,
                    "account_code": "",
                    "description": "An expense account that tracks the amount you repay for construction loans.",
                    "balance": 0.0,
                    "balance_type": "",
                    "date": created_date,
                    "create_status": "default",
                    "status": "active",
                },
                {
                    "company_id": com,
                    "Login_Id": data,
                    "account_type": "Expense",
                    "account_name": "Contract Assets",
                    "credit_card_no": "",
                    "sub_account": "",
                    "parent_account": "",
                    "bank_account_no": None,
                    "account_code": "",
                    "description": "An asset account to track the amount that you receive from your customers while you're yet to complete rendering the services.",
                    "balance": 0.0,
                    "balance_type": "",
                    "date": created_date,
                    "create_status": "default",
                    "status": "active",
                },
                {
                    "company_id": com,
                    "Login_Id": data,
                    "account_type": "Expense",
                    "account_name": "Depreciation And Amortisation",
                    "credit_card_no": "",
                    "sub_account": "",
                    "parent_account": "",
                    "bank_account_no": None,
                    "account_code": "",
                    "description": "An expense account that is used to track the depreciation of tangible assets and intangible assets, which is amortization.",
                    "balance": 0.0,
                    "balance_type": "",
                    "date": created_date,
                    "create_status": "default",
                    "status": "active",
                },
                {
                    "company_id": com,
                    "Login_Id": data,
                    "account_type": "Equity",
                    "account_name": "Distributions",
                    "credit_card_no": "",
                    "sub_account": "",
                    "parent_account": "",
                    "bank_account_no": None,
                    "account_code": "",
                    "description": "An equity account that tracks the payment of stock, cash or physical products to its shareholders.",
                    "balance": 0.0,
                    "balance_type": "",
                    "date": created_date,
                    "create_status": "default",
                    "status": "active",
                },
                {
                    "company_id": com,
                    "Login_Id": data,
                    "account_type": "Equity",
                    "account_name": "Dividends Paid",
                    "credit_card_no": "",
                    "sub_account": "",
                    "parent_account": "",
                    "bank_account_no": None,
                    "account_code": "",
                    "description": "An equity account to track the dividends paid when a corporation declares dividend on its common stock.",
                    "balance": 0.0,
                    "balance_type": "",
                    "date": created_date,
                    "create_status": "default",
                    "status": "active",
                },
                {
                    "company_id": com,
                    "Login_Id": data,
                    "account_type": "Other Current Liability",
                    "account_name": "GST Payable",
                    "credit_card_no": "",
                    "sub_account": "",
                    "parent_account": "",
                    "bank_account_no": None,
                    "account_code": "",
                    "description": "",
                    "balance": 0.0,
                    "balance_type": "",
                    "date": created_date,
                    "create_status": "default",
                    "status": "active",
                },
                {
                    "company_id": com,
                    "Login_Id": data,
                    "account_type": "Other Current Liability",
                    "account_name": "Output CGST",
                    "credit_card_no": "",
                    "sub_account": True,
                    "parent_account": "GST Payable",
                    "bank_account_no": None,
                    "account_code": "",
                    "description": "",
                    "balance": 0.0,
                    "balance_type": "",
                    "date": created_date,
                    "create_status": "default",
                    "status": "active",
                },
                {
                    "company_id": com,
                    "Login_Id": data,
                    "account_type": "Other Current Liability",
                    "account_name": "Output IGST",
                    "credit_card_no": "",
                    "sub_account": True,
                    "parent_account": "GST Payable",
                    "bank_account_no": None,
                    "account_code": "",
                    "description": "",
                    "balance": 0.0,
                    "balance_type": "",
                    "date": created_date,
                    "create_status": "default",
                    "status": "active",
                },
                {
                    "company_id": com,
                    "Login_Id": data,
                    "account_type": "Other Current Liability",
                    "account_name": "Output SGST",
                    "credit_card_no": "",
                    "sub_account": True,
                    "parent_account": "GST Payable",
                    "bank_account_no": None,
                    "account_code": "",
                    "description": "",
                    "balance": 0.0,
                    "balance_type": "",
                    "date": created_date,
                    "create_status": "default",
                    "status": "active",
                },
                {
                    "company_id": com,
                    "Login_Id": data,
                    "account_type": "Other Current Asset",
                    "account_name": "GST TCS Receivable",
                    "credit_card_no": "",
                    "sub_account": "",
                    "parent_account": "",
                    "bank_account_no": None,
                    "account_code": "",
                    "description": "",
                    "balance": 0.0,
                    "balance_type": "",
                    "date": created_date,
                    "create_status": "default",
                    "status": "active",
                },
                {
                    "company_id": com,
                    "Login_Id": data,
                    "account_type": "Other Current Asset",
                    "account_name": "GST TDS Receivable",
                    "credit_card_no": "",
                    "sub_account": "",
                    "parent_account": "",
                    "bank_account_no": None,
                    "account_code": "",
                    "description": "",
                    "balance": 0.0,
                    "balance_type": "",
                    "date": created_date,
                    "create_status": "default",
                    "status": "active",
                },
                {
                    "company_id": com,
                    "Login_Id": data,
                    "account_type": "Other Current Asset",
                    "account_name": "Input Tax Credits",
                    "credit_card_no": "",
                    "sub_account": "",
                    "parent_account": "",
                    "bank_account_no": None,
                    "account_code": "",
                    "description": "",
                    "balance": 0.0,
                    "balance_type": "",
                    "date": created_date,
                    "create_status": "default",
                    "status": "active",
                },
                {
                    "company_id": com,
                    "Login_Id": data,
                    "account_type": "Other Current Asset",
                    "account_name": "Input CGST",
                    "credit_card_no": "",
                    "sub_account": True,
                    "parent_account": "Input Tax Credits",
                    "bank_account_no": None,
                    "account_code": "",
                    "description": "",
                    "balance": 0.0,
                    "balance_type": "",
                    "date": created_date,
                    "create_status": "default",
                    "status": "active",
                },
                {
                    "company_id": com,
                    "Login_Id": data,
                    "account_type": "Other Current Asset",
                    "account_name": "Input IGST",
                    "credit_card_no": "",
                    "sub_account": True,
                    "parent_account": "Input Tax Credits",
                    "bank_account_no": None,
                    "account_code": "",
                    "description": "",
                    "balance": 0.0,
                    "balance_type": "",
                    "date": created_date,
                    "create_status": "default",
                    "status": "active",
                },
                {
                    "company_id": com,
                    "Login_Id": data,
                    "account_type": "Other Current Asset",
                    "account_name": "Input SGST",
                    "credit_card_no": "",
                    "sub_account": True,
                    "parent_account": "Input Tax Credits",
                    "bank_account_no": None,
                    "account_code": "",
                    "description": "",
                    "balance": 0.0,
                    "balance_type": "",
                    "date": created_date,
                    "create_status": "default",
                    "status": "active",
                },
                {
                    "company_id": com,
                    "Login_Id": data,
                    "account_type": "Equity",
                    "account_name": "Investments",
                    "credit_card_no": "",
                    "sub_account": "",
                    "parent_account": "",
                    "bank_account_no": None,
                    "account_code": "",
                    "description": "An equity account used to track the amount that you invest.",
                    "balance": 0.0,
                    "balance_type": "",
                    "date": created_date,
                    "create_status": "default",
                    "status": "active",
                },
                {
                    "company_id": com,
                    "Login_Id": data,
                    "account_type": "Cost Of Goods Sold",
                    "account_name": "Job Costing",
                    "credit_card_no": "",
                    "sub_account": "",
                    "parent_account": "",
                    "bank_account_no": None,
                    "account_code": "",
                    "description": "An expense account to track the costs that you incur in performing a job or a task.",
                    "balance": 0.0,
                    "balance_type": "",
                    "date": created_date,
                    "create_status": "default",
                    "status": "active",
                },
                {
                    "company_id": com,
                    "Login_Id": data,
                    "account_type": "Cost Of Goods Sold",
                    "account_name": "Labor",
                    "credit_card_no": "",
                    "sub_account": "",
                    "parent_account": "",
                    "bank_account_no": None,
                    "account_code": "",
                    "description": "An expense account that tracks the amount that you pay as labor.",
                    "balance": 0.0,
                    "balance_type": "",
                    "date": created_date,
                    "create_status": "default",
                    "status": "active",
                },
                {
                    "company_id": com,
                    "Login_Id": data,
                    "account_type": "Cost Of Goods Sold",
                    "account_name": "Materials",
                    "credit_card_no": "",
                    "sub_account": "",
                    "parent_account": "",
                    "bank_account_no": None,
                    "account_code": "",
                    "description": "An expense account that tracks the amount you use in purchasing materials.",
                    "balance": 0.0,
                    "balance_type": "",
                    "date": created_date,
                    "create_status": "default",
                    "status": "active",
                },
                {
                    "company_id": com,
                    "Login_Id": data,
                    "account_type": "Expense",
                    "account_name": "Merchandise",
                    "credit_card_no": "",
                    "sub_account": "",
                    "parent_account": "",
                    "bank_account_no": None,
                    "account_code": "",
                    "description": "An expense account to track the amount spent on purchasing merchandise.",
                    "balance": 0.0,
                    "balance_type": "",
                    "date": created_date,
                    "create_status": "default",
                    "status": "active",
                },
                {
                    "company_id": com,
                    "Login_Id": data,
                    "account_type": "Long Term Liability",
                    "account_name": "Mortgages",
                    "credit_card_no": "",
                    "sub_account": "",
                    "parent_account": "",
                    "bank_account_no": None,
                    "account_code": "",
                    "description": "An expense account that tracks the amounts you pay for the mortgage loan.",
                    "balance": 0.0,
                    "balance_type": "",
                    "date": created_date,
                    "create_status": "default",
                    "status": "active",
                },
                {
                    "company_id": com,
                    "Login_Id": data,
                    "account_type": "Expense",
                    "account_name": "Raw Materials And Consumables",
                    "credit_card_no": "",
                    "sub_account": "",
                    "parent_account": "",
                    "bank_account_no": None,
                    "account_code": "",
                    "description": "An expense account to track the amount spent on purchasing raw materials and consumables.",
                    "balance": 0.0,
                    "balance_type": "",
                    "date": created_date,
                    "create_status": "default",
                    "status": "active",
                },
                {
                    "company_id": com,
                    "Login_Id": data,
                    "account_type": "Other Current Asset",
                    "account_name": "Reverse Charge Tax Input but not due",
                    "credit_card_no": "",
                    "sub_account": "",
                    "parent_account": "",
                    "bank_account_no": None,
                    "account_code": "",
                    "description": "The amount of tax payable for your reverse charge purchases can be tracked here.",
                    "balance": 0.0,
                    "balance_type": "",
                    "date": created_date,
                    "create_status": "default",
                    "status": "active",
                },
                {
                    "company_id": com,
                    "Login_Id": data,
                    "account_type": "Other Current Asset",
                    "account_name": "Sales to Customers (Cash)",
                    "credit_card_no": "",
                    "sub_account": "",
                    "parent_account": "",
                    "bank_account_no": None,
                    "account_code": "",
                    "description": "",
                    "balance": 0.0,
                    "balance_type": "",
                    "date": created_date,
                    "create_status": "default",
                    "status": "active",
                },
                {
                    "company_id": com,
                    "Login_Id": data,
                    "account_type": "Cost Of Goods Sold",
                    "account_name": "Subcontractor",
                    "credit_card_no": "",
                    "sub_account": "",
                    "parent_account": "",
                    "bank_account_no": None,
                    "account_code": "",
                    "description": " An expense account to track the amount that you pay subcontractors who provide service to you.",
                    "balance": 0.0,
                    "balance_type": "",
                    "date": created_date,
                    "create_status": "default",
                    "status": "active",
                },
                {
                    "company_id": com,
                    "Login_Id": data,
                    "account_type": "Other Current Liability",
                    "account_name": "TDS Payable",
                    "credit_card_no": "",
                    "sub_account": "",
                    "parent_account": "",
                    "bank_account_no": None,
                    "account_code": "",
                    "description": "",
                    "balance": 0.0,
                    "balance_type": "",
                    "date": created_date,
                    "create_status": "default",
                    "status": "active",
                },
                {
                    "company_id": com,
                    "Login_Id": data,
                    "account_type": "Other Current Asset",
                    "account_name": "TDS Receivable",
                    "credit_card_no": "",
                    "sub_account": "",
                    "parent_account": "",
                    "bank_account_no": None,
                    "account_code": "",
                    "description": "",
                    "balance": 0.0,
                    "balance_type": "",
                    "date": created_date,
                    "create_status": "default",
                    "status": "active",
                },
                {
                    "company_id": com,
                    "Login_Id": data,
                    "account_type": "Expense",
                    "account_name": "Transportation Expense",
                    "credit_card_no": "",
                    "sub_account": "",
                    "parent_account": "",
                    "bank_account_no": None,
                    "account_code": "",
                    "description": "An expense account to track the amount spent on transporting goods or providing services.",
                    "balance": 0.0,
                    "balance_type": "",
                    "date": created_date,
                    "create_status": "default",
                    "status": "active",
                },
                {
                    "company_id": com,
                    "Login_Id": data,
                    "account_type": "Bank",
                    "account_name": "Bank Account",
                    "credit_card_no": "",
                    "sub_account": "",
                    "parent_account": "",
                    "bank_account_no": None,
                    "account_code": "",
                    "description": "",
                    "balance": 0.0,
                    "balance_type": "",
                    "date": created_date,
                    "create_status": "default",
                    "status": "active",
                },
                {
                    "company_id": com,
                    "Login_Id": data,
                    "account_type": "Cash",
                    "account_name": "Cash Account",
                    "credit_card_no": "",
                    "sub_account": "",
                    "parent_account": "",
                    "bank_account_no": None,
                    "account_code": "",
                    "description": "",
                    "balance": 0.0,
                    "balance_type": "",
                    "date": created_date,
                    "create_status": "default",
                    "status": "active",
                },
                {
                    "company_id": com,
                    "Login_Id": data,
                    "account_type": "Credit Card",
                    "account_name": "Credit Card Account",
                    "credit_card_no": "",
                    "sub_account": "",
                    "parent_account": "",
                    "bank_account_no": None,
                    "account_code": "",
                    "description": "",
                    "balance": 0.0,
                    "balance_type": "",
                    "date": created_date,
                    "create_status": "default",
                    "status": "active",
                },
                {
                    "company_id": com,
                    "Login_Id": data,
                    "account_type": "Payment Clearing Account",
                    "account_name": "Payment Clearing Account",
                    "credit_card_no": "",
                    "sub_account": "",
                    "parent_account": "",
                    "bank_account_no": None,
                    "account_code": "",
                    "description": "",
                    "balance": 0.0,
                    "balance_type": "",
                    "date": created_date,
                    "create_status": "default",
                    "status": "active",
                },
            ]

            for account in account_info:
                if not Fin_Chart_Of_Account.objects.filter(
                    Company=com, account_name=account["account_name"]
                ).exists():
                    new_account = Fin_Chart_Of_Account(
                        Company=account["company_id"],
                        LoginDetails=account["Login_Id"],
                        account_name=account["account_name"],
                        account_type=account["account_type"],
                        credit_card_no=account["credit_card_no"],
                        sub_account=account["sub_account"],
                        parent_account=account["parent_account"],
                        bank_account_no=account["bank_account_no"],
                        account_code=account["account_code"],
                        description=account["description"],
                        balance=account["balance"],
                        balance_type=account["balance_type"],
                        create_status=account["create_status"],
                        status=account["status"],
                        date=account["date"],
                    )
                    new_account.save()

            # Adding Default Customer payment under company
            Fin_Company_Payment_Terms.objects.create(
                Company=com, term_name="Due on Receipt", days=0
            )
            Fin_Company_Payment_Terms.objects.create(
                Company=com, term_name="NET 30", days=30
            )
            Fin_Company_Payment_Terms.objects.create(
                Company=com, term_name="NET 60", days=60
            )

            # sumayya-------- Adding default repeat every values for company

            Fin_CompanyRepeatEvery.objects.create(
                company=com,
                repeat_every="3 Month",
                repeat_type="Month",
                duration=3,
                days=90,
            )
            Fin_CompanyRepeatEvery.objects.create(
                company=com,
                repeat_every="6 Month",
                repeat_type="Month",
                duration=6,
                days=180,
            )
            Fin_CompanyRepeatEvery.objects.create(
                company=com,
                repeat_every="1 Year",
                repeat_type="Year",
                duration=1,
                days=360,
            )

            # Creating default transport entries with company information---aiswarya
            Fin_Eway_Transportation.objects.create(Name="Bus", Type="Road", Company=com)
            Fin_Eway_Transportation.objects.create(
                Name="Train", Type="Rail", Company=com
            )
            Fin_Eway_Transportation.objects.create(Name="Car", Type="Road", Company=com)

            Stock_Reason.objects.create(
                company=com, login_details=data, reason="Stock on fire"
            )
            Stock_Reason.objects.create(
                company=com, login_details=data, reason="High demand of goods"
            )
            Stock_Reason.objects.create(
                company=com, login_details=data, reason="Stock written off"
            )
            Stock_Reason.objects.create(
                company=com, login_details=data, reason="Inventory Revaluation"
            )

            return Response(
                {"status": True, "data": serializer.data}, status=status.HTTP_200_OK
            )
        else:
            return Response(
                {"status": False, "data": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
    except Fin_Login_Details.DoesNotExist:
        return Response(
            {"status": False, "message": "Login details not found"},
            status=status.HTTP_404_NOT_FOUND,
        )
    except Fin_Company_Details.DoesNotExist:
        return Response(
            {"status": False, "message": "Company details not found"},
            status=status.HTTP_404_NOT_FOUND,
        )
    except Exception as e:
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(("POST",))
def Fin_DReg_Action(request):
    if request.method == "POST":
        if Fin_Login_Details.objects.filter(
            User_name=request.data["User_name"]
        ).exists():
            return Response(
                {
                    "status": False,
                    "message": "This username already exists. Sign up again",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        elif Fin_Company_Details.objects.filter(Email=request.data["Email"]).exists():
            return Response(
                {
                    "status": False,
                    "message": "This email already exists. Sign up again",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        else:
            request.data["User_Type"] = "Distributor"

            serializer = LoginDetailsSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                loginId = Fin_Login_Details.objects.get(id=serializer.data["id"]).id

                code_length = 8
                characters = string.ascii_letters + string.digits  # Letters and numbers

                while True:
                    unique_code = "".join(
                        random.choice(characters) for _ in range(code_length)
                    )
                    # Check if the code already exists in the table
                    if not Fin_Company_Details.objects.filter(
                        Company_Code=unique_code
                    ).exists():
                        break

                request.data["Login_Id"] = loginId
                request.data["Distributor_Code"] = unique_code
                request.data["Admin_approval_status"] = "NULL"

                distributorSerializer = DistributorDetailsSerializer(data=request.data)
                if distributorSerializer.is_valid():
                    distributorSerializer.save()
                    return Response(
                        {"status": True, "data": distributorSerializer.data},
                        status=status.HTTP_201_CREATED,
                    )
                else:
                    return Response(
                        {"status": False, "data": distributorSerializer.errors},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
            else:
                return Response(
                    {"status": False, "data": serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST,
                )


@api_view(["GET"])
def Fin_getPaymentTerms(request):
    try:
        terms = Fin_Payment_Terms.objects.all()
        if terms:
            serializer = PaymentTermsSerializer(terms, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return JsonResponse({"status": False}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
def Fin_getDistributorData(request, id):
    try:
        login_id = id
        data = Fin_Login_Details.objects.get(id=login_id)
        if data:
            distr = Fin_Distributors_Details.objects.get(Login_Id=data)
            dict = {
                "fName": data.First_name,
                "lName": data.Last_name,
                "uName": data.User_name,
                "email": distr.Email,
            }
            return JsonResponse(
                {"status": True, "data": dict}, status=status.HTTP_200_OK
            )
        else:
            return JsonResponse({"status": False}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(("PUT",))
@parser_classes((MultiPartParser, FormParser))
def Fin_DReg2_Action2(request):
    try:
        login_id = request.data["Id"]
        data = Fin_Login_Details.objects.get(id=login_id)
        ddata = Fin_Distributors_Details.objects.get(Login_Id=data)

        serializer = DistributorDetailsSerializer(
            ddata, data=request.data, partial=True
        )
        if serializer.is_valid():
            serializer.save()

            # Update the company with trial period dates
            payment_term = request.data["Payment_Term"]
            terms = Fin_Payment_Terms.objects.get(id=payment_term)

            start_date = date.today()
            days = int(terms.days)
            end = date.today() + timedelta(days=days)

            ddata.Start_Date = start_date
            ddata.End_date = end
            ddata.save()

            return Response(
                {"status": True, "data": serializer.data}, status=status.HTTP_200_OK
            )
        else:
            return Response(
                {"status": False, "data": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

    except Fin_Login_Details.DoesNotExist:
        return Response(
            {"status": False, "message": "Login details not found"},
            status=status.HTTP_404_NOT_FOUND,
        )
    except Fin_Distributors_Details.DoesNotExist:
        return Response(
            {"status": False, "message": "Distributor details not found"},
            status=status.HTTP_404_NOT_FOUND,
        )
    except Exception as e:
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(("POST",))
def Fin_staffReg_action(request):
    if not Fin_Company_Details.objects.filter(
        Company_Code=request.data["Company_code"]
    ).exists():
        return Response(
            {
                "status": False,
                "message": "This company code does not exists. try again.",
            },
            status=status.HTTP_400_BAD_REQUEST,
        )
    elif Fin_Login_Details.objects.filter(User_name=request.data["User_name"]).exists():
        return Response(
            {
                "status": False,
                "message": "This username already exists. Sign up again",
            },
            status=status.HTTP_400_BAD_REQUEST,
        )
    elif Fin_Staff_Details.objects.filter(Email=request.data["Email"]).exists():
        return Response(
            {
                "status": False,
                "message": "This email already exists. Sign up again",
            },
            status=status.HTTP_400_BAD_REQUEST,
        )
    else:
        com = Fin_Company_Details.objects.get(Company_Code=request.data["Company_code"])

        request.data["User_Type"] = "Staff"

        serializer = LoginDetailsSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            loginId = Fin_Login_Details.objects.get(id=serializer.data["id"]).id

            request.data["Login_Id"] = loginId
            request.data["Company_approval_status"] = "Null"
            request.data["company_id"] = com.id
            staffSerializer = StaffDetailsSerializer(data=request.data)
            if staffSerializer.is_valid():
                staffSerializer.save()
                return Response(
                    {"status": True, "data": staffSerializer.data},
                    status=status.HTTP_201_CREATED,
                )
            else:
                return Response(
                    {"status": False, "data": staffSerializer.errors},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        else:
            return Response(
                {"status": False, "data": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )


@api_view(["GET"])
def Fin_getStaffData(request, id):
    try:
        login_id = id
        data = Fin_Login_Details.objects.get(id=login_id)
        if data:
            stf = Fin_Staff_Details.objects.get(Login_Id=data)
            dict = {
                "name": data.First_name + " " + data.Last_name,
                "uName": data.User_name,
                "email": stf.Email,
            }
            return JsonResponse(
                {"status": True, "data": dict}, status=status.HTTP_200_OK
            )
        else:
            return JsonResponse({"status": False}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(("PUT",))
@parser_classes((MultiPartParser, FormParser))
def Fin_StaffReg2_Action(request):
    try:
        login_id = request.data["Id"]
        data = Fin_Login_Details.objects.get(id=login_id)
        sdata = Fin_Staff_Details.objects.get(Login_Id=data)

        serializer = StaffDetailsSerializer(sdata, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()

            return Response(
                {"status": True, "data": serializer.data}, status=status.HTTP_200_OK
            )
        else:
            return Response(
                {"status": False, "data": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

    except Fin_Login_Details.DoesNotExist:
        return Response(
            {"status": False, "message": "Login details not found"},
            status=status.HTTP_404_NOT_FOUND,
        )
    except Fin_Staff_Details.DoesNotExist:
        return Response(
            {"status": False, "message": "Staff details not found"},
            status=status.HTTP_404_NOT_FOUND,
        )
    except Exception as e:
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(("POST",))
def Fin_login(request):
    try:
        user_name = request.data["username"]
        passw = request.data["password"]

        log_user = auth.authenticate(username=user_name, password=passw)

        if log_user is not None:
            auth.login(request, log_user)

            # ---super admin---

            if request.user.is_staff == 1:
                return Response(
                    {
                        "status": True,
                        "redirect": "admin_home",
                        "user": "Admin",
                        "Login_id": "",
                    },
                    status=status.HTTP_200_OK,
                )

        # -------distributor ------

        if Fin_Login_Details.objects.filter(
            User_name=user_name, password=passw
        ).exists():
            data = Fin_Login_Details.objects.get(User_name=user_name, password=passw)
            if data.User_Type == "Distributor":
                did = Fin_Distributors_Details.objects.get(Login_Id=data.id)
                if did.Admin_approval_status == "Accept":
                    request.session["s_id"] = data.id
                    current_day = date.today()
                    if current_day > did.End_date:
                        print("wrong")

                        if not Fin_Payment_Terms_updation.objects.filter(
                            Login_Id=data, status="New"
                        ).exists():
                            return Response(
                                {
                                    "status": False,
                                    "redirect": "wrong",
                                    "message": "Terms Expired",
                                }
                            )
                        else:
                            return Response(
                                {
                                    "status": False,
                                    "redirect": "distributor_registration",
                                    "message": "Term Updation Request is pending..",
                                }
                            )
                    else:
                        return Response(
                            {
                                "status": True,
                                "redirect": "distributor_home",
                                "user": "Distributor",
                                "Login_id": data.id,
                            },
                            status=status.HTTP_200_OK,
                        )

                else:
                    return Response(
                        {"status": False, "message": "Approval is Pending"},
                        status=status.HTTP_404_NOT_FOUND,
                    )

            if data.User_Type == "Company":
                cid = Fin_Company_Details.objects.get(Login_Id=data.id)
                if (
                    cid.Admin_approval_status == "Accept"
                    or cid.Distributor_approval_status == "Accept"
                ):
                    request.session["s_id"] = data.id

                    com = Fin_Company_Details.objects.get(Login_Id=data.id)

                    current_day = date.today()
                    if current_day > com.End_date:
                        print("wrong")

                        if not Fin_Payment_Terms_updation.objects.filter(
                            Login_Id=data, status="New"
                        ).exists():
                            return Response(
                                {
                                    "status": False,
                                    "redirect": "wrong",
                                    "message": "Terms Expired",
                                }
                            )
                        else:
                            return Response(
                                {
                                    "status": False,
                                    "redirect": "company_registration",
                                    "message": "Term Updation Request is pending..",
                                }
                            )

                    else:
                        return Response(
                            {
                                "status": True,
                                "redirect": "company_home",
                                "user": "Company",
                                "Login_id": data.id,
                            },
                            status=status.HTTP_200_OK,
                        )
                else:
                    return Response(
                        {"status": False, "message": "Approval is Pending"},
                        status=status.HTTP_404_NOT_FOUND,
                    )

            if data.User_Type == "Staff":
                cid = Fin_Staff_Details.objects.get(Login_Id=data.id)
                if cid.Company_approval_status == "Accept":
                    request.session["s_id"] = data.id
                    com = Fin_Staff_Details.objects.get(Login_Id=data.id)

                    current_day = date.today()
                    if current_day > com.company_id.End_date:
                        print("wrong")
                        return Response(
                            {
                                "status": False,
                                "redirect": "staff_registration",
                                "message": "Your account is temporarily blocked",
                            }
                        )
                    else:
                        return Response(
                            {
                                "status": True,
                                "redirect": "company_home",
                                "user": "Staff",
                                "Login_id": data.id,
                            },
                            status=status.HTTP_200_OK,
                        )
                else:
                    return Response(
                        {"status": False, "message": "Approval is Pending"},
                        status=status.HTTP_404_NOT_FOUND,
                    )

        else:
            return Response(
                {"status": False, "message": "Invalid username or password, try again"},
                status=status.HTTP_404_NOT_FOUND,
            )
    except Exception as e:
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(("POST",))
def Fin_add_payment_terms(request):
    try:
        num = int(request.data["num"])
        select = request.data["value"]
        if select == "Years":
            days = int(num) * 365
            pt = Fin_Payment_Terms(
                payment_terms_number=num, payment_terms_value=select, days=days
            )
            pt.save()
            return Response({"status": True}, status=status.HTTP_201_CREATED)
        else:
            days = int(num * 30)
            pt = Fin_Payment_Terms(
                payment_terms_number=num, payment_terms_value=select, days=days
            )
            pt.save()
            return Response({"status": True}, status=status.HTTP_201_CREATED)
    except Exception as e:
        print(e)
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(("DELETE",))
def Fin_delete_payment_terms(request, id):
    try:
        term = Fin_Payment_Terms.objects.get(id=id)
        term.delete()
        return Response({"status": True}, status=status.HTTP_201_CREATED)
    except Exception as e:
        print(e)
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(("GET",))
def Fin_getDistributorsRequests(request):
    try:
        data = Fin_Distributors_Details.objects.filter(Admin_approval_status="NULL")
        # serializer = DistributorDetailsSerializer(data, many=True)
        requests = []
        for i in data:
            req = {
                "id": i.id,
                "name": i.Login_Id.First_name + " " + i.Login_Id.Last_name,
                "email": i.Email,
                "contact": i.Contact,
                "term": (
                    str(i.Payment_Term.payment_terms_number)
                    + " "
                    + i.Payment_Term.payment_terms_value
                    if i.Payment_Term
                    else ""
                ),
                "endDate": i.End_date,
            }
            requests.append(req)
        print("DIST DATA==", requests)
        return Response({"status": True, "data": requests})
    except Exception as e:
        print(e)
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(("GET",))
def Fin_getDistributors(request):
    try:
        data = Fin_Distributors_Details.objects.filter(Admin_approval_status="Accept")
        # serializer = DistributorDetailsSerializer(data, many=True)
        requests = []
        for i in data:
            req = {
                "id": i.id,
                "name": i.Login_Id.First_name + " " + i.Login_Id.Last_name,
                "email": i.Email,
                "contact": i.Contact,
                "term": (
                    str(i.Payment_Term.payment_terms_number)
                    + " "
                    + i.Payment_Term.payment_terms_value
                    if i.Payment_Term
                    else ""
                ),
                "endDate": i.End_date,
            }
            requests.append(req)

        return Response({"status": True, "data": requests})
    except Exception as e:
        print(e)
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(("PUT",))
def Fin_DReq_Accept(request, id):
    try:
        data = Fin_Distributors_Details.objects.get(id=id)
        data.Admin_approval_status = "Accept"
        data.save()
        return Response({"status": True}, status=status.HTTP_200_OK)
    except Fin_Distributors_Details.DoesNotExist:
        return Response(
            {"status": False, "message": "Distributor details not found"},
            status=status.HTTP_404_NOT_FOUND,
        )
    except Exception as e:
        print(e)
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(("DELETE",))
def Fin_DReq_Reject(request, id):
    print("session", request.session)
    try:
        data = Fin_Distributors_Details.objects.get(id=id)
        data.Login_Id.delete()
        data.delete()
        return Response({"status": True}, status=status.HTTP_200_OK)
    except Fin_Distributors_Details.DoesNotExist:
        return Response(
            {"status": False, "message": "Distributor details not found"},
            status=status.HTTP_404_NOT_FOUND,
        )
    except Exception as e:
        print(e)
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(("GET",))
def Fin_getDistributorsOverviewData(request, id):
    try:
        data = Fin_Distributors_Details.objects.get(id=id)
        # serializer = DistributorDetailsSerializer(data, many=True)
        req = {
            "id": data.id,
            "name": data.Login_Id.First_name + " " + data.Login_Id.Last_name,
            "email": data.Email,
            "code": data.Distributor_Code,
            "contact": data.Contact,
            "username": data.Login_Id.User_name,
            "image": data.Image.url if data.Image else None,
            "endDate": data.End_date,
            "term": (
                str(data.Payment_Term.payment_terms_number)
                + " "
                + data.Payment_Term.payment_terms_value
                if data.Payment_Term
                else ""
            ),
        }
        return Response({"status": True, "data": req}, status=status.HTTP_200_OK)
    except Fin_Distributors_Details.DoesNotExist:
        return Response(
            {"status": False, "message": "Distributor details not found"},
            status=status.HTTP_404_NOT_FOUND,
        )
    except Exception as e:
        print(e)
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(("GET",))
def Fin_getClientsRequests(request):
    try:
        data = Fin_Company_Details.objects.filter(
            Registration_Type="self", Admin_approval_status="NULL"
        )
        requests = []
        for i in data:
            req = {
                "id": i.id,
                "name": i.Login_Id.First_name + " " + i.Login_Id.Last_name,
                "email": i.Email,
                "contact": i.Contact,
                "term": (
                    str(i.Payment_Term.payment_terms_number)
                    + " "
                    + i.Payment_Term.payment_terms_value
                    if i.Payment_Term
                    else "Trial Period"
                ),
                "endDate": i.End_date,
            }
            requests.append(req)

        return Response({"status": True, "data": requests})
    except Exception as e:
        print(e)
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(("PUT",))
def Fin_Client_Req_Accept(request, id):
    try:
        data = Fin_Company_Details.objects.get(id=id)
        data.Admin_approval_status = "Accept"
        data.save()
        return Response({"status": True}, status=status.HTTP_200_OK)
    except Fin_Company_Details.DoesNotExist:
        return Response(
            {"status": False, "message": "Client details not found"},
            status=status.HTTP_404_NOT_FOUND,
        )
    except Exception as e:
        print(e)
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(("DELETE",))
def Fin_Client_Req_Reject(request, id):
    try:
        data = Fin_Company_Details.objects.get(id=id)
        data.Login_Id.delete()
        data.delete()
        return Response({"status": True}, status=status.HTTP_200_OK)
    except Fin_Company_Details.DoesNotExist:
        return Response(
            {"status": False, "message": "Client details not found"},
            status=status.HTTP_404_NOT_FOUND,
        )
    except Exception as e:
        print(e)
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(("GET",))
def Fin_getClients(request):
    try:
        data = Fin_Company_Details.objects.filter(Admin_approval_status="Accept")
        # serializer = DistributorDetailsSerializer(data, many=True)
        requests = []
        for i in data:
            req = {
                "id": i.id,
                "name": i.Login_Id.First_name + " " + i.Login_Id.Last_name,
                "email": i.Email,
                "contact": i.Contact,
                "term": (
                    str(i.Payment_Term.payment_terms_number)
                    + " "
                    + i.Payment_Term.payment_terms_value
                    if i.Payment_Term
                    else "Trial Period"
                ),
                "endDate": i.End_date,
            }
            requests.append(req)

        return Response({"status": True, "data": requests})
    except Exception as e:
        print(e)
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(("GET",))
def Fin_getClientsOverviewData(request, id):
    try:
        data = Fin_Company_Details.objects.get(id=id)
        modules = Fin_Modules_List.objects.get(company_id=id, status="New")
        serializer = ModulesListSerializer(modules)
        req = {
            "id": data.id,
            "name": data.Login_Id.First_name + " " + data.Login_Id.Last_name,
            "email": data.Email,
            "code": data.Company_Code,
            "contact": data.Contact,
            "username": data.Login_Id.User_name,
            "image": data.Image.url if data.Image else "",
            "endDate": data.End_date,
            "term": (
                str(data.Payment_Term.payment_terms_number)
                + " "
                + data.Payment_Term.payment_terms_value
                if data.Payment_Term
                else "Trial Period"
            ),
        }
        return Response(
            {"status": True, "data": req, "modules": serializer.data},
            status=status.HTTP_200_OK,
        )
    except Fin_Company_Details.DoesNotExist:
        return Response(
            {"status": False, "message": "Client details not found"},
            status=status.HTTP_404_NOT_FOUND,
        )
    except Exception as e:
        print(e)
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(("GET",))
def Fin_DClient_req(request, id):
    try:
        data = Fin_Distributors_Details.objects.get(Login_Id=id)
        lst = Fin_Company_Details.objects.filter(
            Registration_Type="distributor",
            Distributor_approval_status="NULL",
            Distributor_id=data.id,
        )
        requests = []
        for i in lst:
            req = {
                "id": i.id,
                "name": i.Login_Id.First_name + " " + i.Login_Id.Last_name,
                "email": i.Email,
                "contact": i.Contact,
                "term": (
                    str(i.Payment_Term.payment_terms_number)
                    + " "
                    + i.Payment_Term.payment_terms_value
                    if i.Payment_Term
                    else "Trial Period"
                ),
                "endDate": i.End_date,
            }
            requests.append(req)

        return Response({"status": True, "data": requests})
    except Exception as e:
        print(e)
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(("GET",))
def Fin_DClients(request, id):
    try:
        data = Fin_Distributors_Details.objects.get(Login_Id=id)
        lst = Fin_Company_Details.objects.filter(
            Registration_Type="distributor",
            Distributor_approval_status="Accept",
            Distributor_id=data.id,
        )
        requests = []
        for i in lst:
            req = {
                "id": i.id,
                "name": i.Login_Id.First_name + " " + i.Login_Id.Last_name,
                "email": i.Email,
                "contact": i.Contact,
                "term": (
                    str(i.Payment_Term.payment_terms_number)
                    + " "
                    + i.Payment_Term.payment_terms_value
                    if i.Payment_Term
                    else "Trial Period"
                ),
                "endDate": i.End_date,
            }
            requests.append(req)

        return Response({"status": True, "data": requests})
    except Exception as e:
        print(e)
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(("PUT",))
def Fin_DClient_Req_Accept(request, id):
    try:
        data = Fin_Company_Details.objects.get(id=id)
        data.Distributor_approval_status = "Accept"
        data.save()
        return Response({"status": True}, status=status.HTTP_200_OK)
    except Fin_Company_Details.DoesNotExist:
        return Response(
            {"status": False, "message": "Client details not found"},
            status=status.HTTP_404_NOT_FOUND,
        )
    except Exception as e:
        print(e)
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(("DELETE",))
def Fin_DClient_Req_Reject(request, id):
    try:
        data = Fin_Company_Details.objects.get(id=id)
        data.Login_Id.delete()
        data.delete()
        return Response({"status": True}, status=status.HTTP_200_OK)
    except Fin_Company_Details.DoesNotExist:
        return Response(
            {"status": False, "message": "Client details not found"},
            status=status.HTTP_404_NOT_FOUND,
        )
    except Exception as e:
        print(e)
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(("GET",))
def getSelfData(request, id):
    try:
        data = Fin_Login_Details.objects.get(id=id)
        img = None
        name = None
        if data.User_Type == "Company":
            usrData = Fin_Company_Details.objects.get(Login_Id=data)
            img = usrData.Image.url if usrData.Image else None
            name = usrData.Company_name
        elif data.User_Type == "Distributor":
            usrData = Fin_Distributors_Details.objects.get(Login_Id=data)
            img = usrData.Image.url if usrData.Image else None
            name = data.First_name + " " + data.Last_name
        elif data.User_Type == "Staff":
            usrData = Fin_Staff_Details.objects.get(Login_Id=data)
            img = usrData.img.url if usrData.img else None
            name = data.First_name + " " + data.Last_name
        else:
            usrData = None

        details = {"name": name, "image": img}

        return Response({"status": True, "data": details})
    except Exception as e:
        print(e)
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(("GET",))
def Fin_getStaffRequests(request, id):
    try:
        # data = Fin_Login_Details.objects.get(id=id)
        com = Fin_Company_Details.objects.get(Login_Id=id)
        data1 = Fin_Staff_Details.objects.filter(
            company_id=com.id, Company_approval_status="NULL"
        )
        requests = []
        for i in data1:
            req = {
                "id": i.id,
                "name": i.Login_Id.First_name + " " + i.Login_Id.Last_name,
                "email": i.Email,
                "contact": i.contact,
                "username": i.Login_Id.User_name,
            }
            requests.append(req)

        return Response({"status": True, "data": requests})
    except Exception as e:
        print(e)
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(("GET",))
def Fin_getAllStaffs(request, id):
    try:
        # data = Fin_Login_Details.objects.get(id=id)
        com = Fin_Company_Details.objects.get(Login_Id=id)
        data1 = Fin_Staff_Details.objects.filter(
            company_id=com.id, Company_approval_status="Accept"
        )
        requests = []
        for i in data1:
            req = {
                "id": i.id,
                "name": i.Login_Id.First_name + " " + i.Login_Id.Last_name,
                "email": i.Email,
                "contact": i.contact,
                "username": i.Login_Id.User_name,
            }
            requests.append(req)

        return Response({"status": True, "data": requests})
    except Exception as e:
        print(e)
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(("PUT",))
def Fin_Staff_Req_Accept(request, id):
    try:
        data = Fin_Staff_Details.objects.get(id=id)
        data.Company_approval_status = "Accept"
        data.save()
        return Response({"status": True}, status=status.HTTP_200_OK)
    except Fin_Staff_Details.DoesNotExist:
        return Response(
            {"status": False, "message": "Staff details not found"},
            status=status.HTTP_404_NOT_FOUND,
        )
    except Exception as e:
        print(e)
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(("DELETE",))
def Fin_Staff_Req_Reject(request, id):
    try:
        data = Fin_Staff_Details.objects.get(id=id)
        data.Login_Id.delete()
        data.delete()
        return Response({"status": True}, status=status.HTTP_200_OK)
    except Fin_Staff_Details.DoesNotExist:
        return Response(
            {"status": False, "message": "Staff details not found"},
            status=status.HTTP_404_NOT_FOUND,
        )
    except Exception as e:
        print(e)
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(("GET",))
def getProfileData(request, id):
    try:
        data = Fin_Login_Details.objects.get(id=id)
        if data.User_Type == "Company":
            usrData = Fin_Company_Details.objects.get(Login_Id=data)
            payment_request = Fin_Payment_Terms_updation.objects.filter(
                Login_Id=data, status="New"
            ).exists()
            personal = {
                "companyLogo": usrData.Image.url if usrData.Image else False,
                "userImage": False,
                "firstName": data.First_name,
                "lastName": data.Last_name,
                "email": usrData.Email,
                "username": data.User_name,
                "companyContact": usrData.Contact,
                "userContact": "",
            }
            company = {
                "businessName": usrData.Business_name,
                "companyName": usrData.Company_name,
                "companyType": usrData.Company_Type,
                "industry": usrData.Industry,
                "companyCode": usrData.Company_Code,
                "companyEmail": usrData.Email,
                "panNumber": usrData.Pan_NO,
                "gstType": usrData.GST_Type,
                "gstNo": usrData.GST_NO,
                "paymentTerm": (
                    str(usrData.Payment_Term.payment_terms_number)
                    + " "
                    + usrData.Payment_Term.payment_terms_value
                    if usrData.Payment_Term
                    else "Trial Period"
                ),
                "endDate": usrData.End_date,
                "address": usrData.Address,
                "city": usrData.City,
                "state": usrData.State,
                "pincode": usrData.Pincode,
            }

        if data.User_Type == "Staff":
            staffData = Fin_Staff_Details.objects.get(Login_Id=data)
            payment_request = Fin_Payment_Terms_updation.objects.filter(
                Login_Id=staffData.company_id.Login_Id, status="New"
            ).exists()

            personal = {
                "companyLogo": False,
                "userImage": staffData.img.url if staffData.img else False,
                "firstName": data.First_name,
                "lastName": data.Last_name,
                "email": staffData.Email,
                "username": data.User_name,
                "companyContact": staffData.company_id.Contact,
                "userContact": staffData.contact,
            }
            company = {
                "businessName": staffData.company_id.Business_name,
                "companyName": staffData.company_id.Company_name,
                "companyType": staffData.company_id.Company_Type,
                "industry": staffData.company_id.Industry,
                "companyCode": staffData.company_id.Company_Code,
                "companyEmail": staffData.company_id.Email,
                "panNumber": staffData.company_id.Pan_NO,
                "gstType": staffData.company_id.GST_Type,
                "gstNo": staffData.company_id.GST_NO,
                "paymentTerm": (
                    str(staffData.company_id.Payment_Term.payment_terms_number)
                    + " "
                    + staffData.company_id.Payment_Term.payment_terms_value
                    if staffData.company_id.Payment_Term
                    else "Trial Period"
                ),
                "endDate": staffData.company_id.End_date,
                "address": staffData.company_id.Address,
                "city": staffData.company_id.City,
                "state": staffData.company_id.State,
                "pincode": staffData.company_id.Pincode,
            }

        return Response(
            {
                "status": True,
                "personalData": personal,
                "companyData": company,
                "payment_request": payment_request,
            },
            status=status.HTTP_200_OK,
        )
    except Exception as e:
        print(e)
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(("PUT",))
@parser_classes((MultiPartParser, FormParser))
def Fin_editCompanyProfile(request):
    try:
        login_id = request.data["Id"]
        data = Fin_Login_Details.objects.get(id=login_id)
        com = Fin_Company_Details.objects.get(Login_Id=data.id)

        logSerializer = LoginDetailsSerializer(data, data=request.data)
        serializer = CompanyDetailsSerializer(com, data=request.data, partial=True)
        if logSerializer.is_valid():
            logSerializer.save()
            if serializer.is_valid():
                serializer.save()
                return Response(
                    {"status": True, "data": serializer.data}, status=status.HTTP_200_OK
                )
            else:
                return Response(
                    {"status": False, "data": serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        else:
            return Response(
                {"status": False, "data": logSerializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

    except Fin_Login_Details.DoesNotExist:
        return Response(
            {"status": False, "message": "Login details not found"},
            status=status.HTTP_404_NOT_FOUND,
        )
    except Fin_Company_Details.DoesNotExist:
        return Response(
            {"status": False, "message": "Company details not found"},
            status=status.HTTP_404_NOT_FOUND,
        )
    except Exception as e:
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(("PUT",))
@parser_classes((MultiPartParser, FormParser))
def Fin_editStaffProfile(request):
    try:
        login_id = request.data["Id"]
        data = Fin_Login_Details.objects.get(id=login_id)
        stf = Fin_Staff_Details.objects.get(Login_Id=data.id)

        logSerializer = LoginDetailsSerializer(data, data=request.data)
        serializer = StaffDetailsSerializer(stf, data=request.data, partial=True)
        if logSerializer.is_valid():
            logSerializer.save()
            if serializer.is_valid():
                serializer.save()
                return Response(
                    {"status": True, "data": serializer.data}, status=status.HTTP_200_OK
                )
            else:
                return Response(
                    {"status": False, "data": serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        else:
            return Response(
                {"status": False, "data": logSerializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

    except Fin_Login_Details.DoesNotExist:
        return Response(
            {"status": False, "message": "Login details not found"},
            status=status.HTTP_404_NOT_FOUND,
        )
    except Fin_Staff_Details.DoesNotExist:
        return Response(
            {"status": False, "message": "Staff details not found"},
            status=status.HTTP_404_NOT_FOUND,
        )
    except Exception as e:
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(("POST",))
def company_gsttype_change(request):
    try:
        s_id = request.data["ID"]
        data = Fin_Login_Details.objects.get(id=s_id)
        com = Fin_Company_Details.objects.get(Login_Id=s_id)

        # Get data from the form

        # gstno = request.POST.get('gstno')
        gsttype = request.data["gsttype"]

        com.GST_Type = gsttype

        com.save()

        # Check if gsttype is one of the specified values
        if gsttype in ["unregistered Business", "Overseas", "Consumer"]:
            com.GST_NO = ""
            com.save()
            return Response(
                {"status": True, "message": "GST Type changed"},
                status=status.HTTP_200_OK,
            )
        else:
            return Response(
                {"status": True, "message": "GST Type changed, add GST Number"},
                status=status.HTTP_200_OK,
            )
    except Exception as e:
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(("POST",))
def Fin_Change_payment_terms(request):
    try:
        s_id = request.data["ID"]
        data = Fin_Login_Details.objects.get(id=s_id)
        com = Fin_Company_Details.objects.get(Login_Id=s_id)
        pt = request.data["payment_term"]

        pay = Fin_Payment_Terms.objects.get(id=pt)

        data1 = Fin_Payment_Terms_updation(Login_Id=data, Payment_Term=pay)
        data1.save()

        if com.Registration_Type == "self":
            noti = Fin_ANotification(
                Login_Id=data,
                PaymentTerms_updation=data1,
                Title="Change Payment Terms",
                Discription=com.Company_name + " wants to subscribe a new plan",
            )
            noti.save()
        else:
            noti = Fin_DNotification(
                Distributor_id=com.Distributor_id,
                Login_Id=data,
                PaymentTerms_updation=data1,
                Title="Change Payment Terms",
                Discription=com.Company_name + " wants to subscribe a new plan",
            )
            noti.save()

        return Response(
            {"status": True, "message": "Request Sent.!"}, status=status.HTTP_200_OK
        )
    except Exception as e:
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(("GET",))
def getDistributorProfileData(request, id):
    try:
        data = Fin_Login_Details.objects.get(id=id)
        usrData = Fin_Distributors_Details.objects.get(Login_Id=data)
        payment_request = Fin_Payment_Terms_updation.objects.filter(
            Login_Id=data, status="New"
        ).exists()
        personal = {
            "userImage": usrData.Image.url if usrData.Image else False,
            "distributorCode": usrData.Distributor_Code,
            "firstName": data.First_name,
            "lastName": data.Last_name,
            "email": usrData.Email,
            "username": data.User_name,
            "userContact": usrData.Contact,
            "joinDate": usrData.Start_Date,
            "paymentTerm": (
                str(usrData.Payment_Term.payment_terms_number)
                + " "
                + usrData.Payment_Term.payment_terms_value
                if usrData.Payment_Term
                else ""
            ),
            "endDate": usrData.End_date,
        }

        return Response(
            {
                "status": True,
                "personalData": personal,
                "payment_request": payment_request,
            },
            status=status.HTTP_200_OK,
        )
    except Exception as e:
        print(e)
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(("POST",))
def Fin_Change_distributor_payment_terms(request):
    try:
        s_id = request.data["ID"]
        data = Fin_Login_Details.objects.get(id=s_id)
        com = Fin_Distributors_Details.objects.get(Login_Id=s_id)
        pt = request.data["payment_term"]

        pay = Fin_Payment_Terms.objects.get(id=pt)

        data1 = Fin_Payment_Terms_updation(Login_Id=data, Payment_Term=pay)
        data1.save()

        noti = Fin_ANotification(
            Login_Id=data,
            PaymentTerms_updation=data1,
            Title="Change Payment Terms",
            Discription=com.Login_Id.First_name
            + " "
            + com.Login_Id.Last_name
            + " wants to subscribe a new plan",
        )
        noti.save()

        return Response(
            {"status": True, "message": "Request Sent.!"}, status=status.HTTP_200_OK
        )
    except Exception as e:
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(("PUT",))
@parser_classes((MultiPartParser, FormParser))
def Fin_editDistributorProfile(request):
    try:
        login_id = request.data["Id"]
        data = Fin_Login_Details.objects.get(id=login_id)
        distr = Fin_Distributors_Details.objects.get(Login_Id=data.id)

        logSerializer = LoginDetailsSerializer(data, data=request.data)
        serializer = DistributorDetailsSerializer(
            distr, data=request.data, partial=True
        )
        if logSerializer.is_valid():
            logSerializer.save()
            if serializer.is_valid():
                serializer.save()
                return Response(
                    {"status": True, "data": serializer.data}, status=status.HTTP_200_OK
                )
            else:
                return Response(
                    {"status": False, "data": serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        else:
            return Response(
                {"status": False, "data": logSerializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

    except Fin_Login_Details.DoesNotExist:
        return Response(
            {"status": False, "message": "Login details not found"},
            status=status.HTTP_404_NOT_FOUND,
        )
    except Fin_Distributors_Details.DoesNotExist:
        return Response(
            {"status": False, "message": "Distributor details not found"},
            status=status.HTTP_404_NOT_FOUND,
        )
    except Exception as e:
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(("GET",))
def Fin_checkPaymentTerms(request, id):
    try:
        s_id = id
        data = Fin_Login_Details.objects.get(id=s_id)
        if data.User_Type == "Company":
            com = Fin_Company_Details.objects.get(Login_Id=s_id)
            payment_request = Fin_Payment_Terms_updation.objects.filter(
                Login_Id=com.Login_Id, status="New"
            ).exists()

            title2 = ["Modules Updated..!", "New Plan Activated..!"]
            today_date = date.today()
            notification = Fin_CNotification.objects.filter(
                status="New", Company_id=com, Title__in=title2, Noti_date__lt=today_date
            ).order_by("-id", "-Noti_date")
            notification.update(status="old")

            diff = (com.End_date - today_date).days

            # payment term and trial period alert notifications for notification page
            cmp_name = com.Company_name
            if com.Payment_Term:
                if (
                    not Fin_CNotification.objects.filter(
                        Company_id=com, Title="Payment Terms Alert", status="New"
                    ).exists()
                    and diff <= 20
                ):

                    n = Fin_CNotification(
                        Login_Id=data,
                        Company_id=com,
                        Title="Payment Terms Alert",
                        Discription="Your Payment Terms End Soon",
                    )
                    n.save()
                    if com.Registration_Type == "self":
                        d = Fin_ANotification(
                            Login_Id=data,
                            Title="Payment Terms Alert",
                            Discription=f"Current  payment terms of {cmp_name} is expiring",
                        )
                    else:
                        d = Fin_DNotification(
                            Login_Id=data,
                            Distributor_id=com.Distributor_id,
                            Title="Payment Terms Alert",
                            Discription=f"Current  payment terms of {cmp_name} is expiring",
                        )

                    d.save()
            else:
                if (
                    not Fin_CNotification.objects.filter(
                        Company_id=com, Title="Trial Period Alert", status="New"
                    ).exists()
                    and diff <= 10
                ):
                    n = Fin_CNotification(
                        Login_Id=data,
                        Company_id=com,
                        Title="Trial Period Alert",
                        Discription="Your Trial Period End Soon",
                    )
                    n.save()
                    print("NOTIFICATION SAVED>>>")
                    if com.Registration_Type == "self":
                        d = Fin_ANotification(
                            Login_Id=data,
                            Title="Payment Terms Alert",
                            Discription=f"Current  payment terms of {cmp_name} is expiring",
                        )
                    else:
                        d = Fin_DNotification(
                            Login_Id=data,
                            Distributor_id=com.Distributor_id,
                            Title="Payment Terms Alert",
                            Discription=f"Current  payment terms of {cmp_name} is expiring",
                        )

                    d.save()

            # Calculate the date 20 days before the end date for payment term renew and 10 days before for trial period renew
            if com.Payment_Term:
                term = True
                reminder_date = com.End_date - timedelta(days=20)
            else:
                term = False
                reminder_date = com.End_date - timedelta(days=10)
            current_date = date.today()
            alert_message = current_date >= reminder_date

            # Calculate the number of days between the reminder date and end date
            days_left = (com.End_date - current_date).days
            return Response(
                {
                    "status": True,
                    "alert_message": alert_message,
                    "endDate": com.End_date,
                    "days_left": days_left,
                    "paymentTerm": term,
                    "payment_request": payment_request,
                    "companyName": cmp_name,
                },
                status=status.HTTP_200_OK,
            )
        else:
            com = Fin_Staff_Details.objects.get(Login_Id=s_id).company_id
            return Response(
                {"status": True, "companyName": com.Company_name},
                status=status.HTTP_200_OK,
            )
    except Exception as e:
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(("GET",))
def Fin_fetchNotifications(request, id):
    try:
        s_id = id
        data = Fin_Login_Details.objects.get(id=s_id)
        if data.User_Type == "Company":
            com = Fin_Company_Details.objects.get(Login_Id=s_id)
            noti = Fin_CNotification.objects.filter(
                status="New", Company_id=com
            ).order_by("-id", "-Noti_date")
            serializer = CNotificationsSerializer(noti, many=True)
            return Response(
                {"status": True, "notifications": serializer.data, 'count':len(noti)},
                status=status.HTTP_200_OK,
            )
        else:
            com = Fin_Staff_Details.objects.get(Login_Id=s_id).company_id
            nCount = Fin_CNotification.objects.filter(Company_id = com, status = 'New')
            return Response(
                {"status": True, "notifications": None, 'count':len(nCount)}, status=status.HTTP_200_OK
            )
    except Exception as e:
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(("GET",))
def Fin_fetchDistNotifications(request, id):
    try:
        s_id = id
        data = Fin_Login_Details.objects.get(id=s_id)
        com = Fin_Distributors_Details.objects.get(Login_Id=s_id)
        noti = Fin_DNotification.objects.filter(
            status="New", Distributor_id=com.id
        ).order_by("-id", "-Noti_date")
        serializer = DNotificationsSerializer(noti, many=True)
        return Response(
            {"status": True, "notifications": serializer.data},
            status=status.HTTP_200_OK,
        )
    except Exception as e:
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(("GET",))
def Fin_checkDistributorPaymentTerms(request, id):
    try:
        s_id = id
        data = Fin_Login_Details.objects.get(id=s_id)
        com = Fin_Distributors_Details.objects.get(Login_Id=s_id)
        payment_request = Fin_Payment_Terms_updation.objects.filter(
            Login_Id=com.Login_Id, status="New"
        ).exists()

        title2 = ["Modules Updated..!", "New Plan Activated..!", "Change Payment Terms"]
        today_date = date.today()
        notification = Fin_DNotification.objects.filter(
            status="New", Distributor_id=com, Title__in=title2, Noti_date__lt=today_date
        )
        notification.update(status="old")

        diff = (com.End_date - today_date).days

        # payment term and trial period alert notifications for notification page
        dis_name = com.Login_Id.First_name + "  " + com.Login_Id.Last_name
        if (
            not Fin_DNotification.objects.filter(
                Login_Id=com.Login_Id,
                Distributor_id=com,
                Title="Payment Terms Alert",
                status="New",
            ).exists()
            and diff <= 20
        ):
            n = Fin_DNotification(
                Login_Id=com.Login_Id,
                Distributor_id=com,
                Title="Payment Terms Alert",
                Discription="Your Payment Terms End Soon",
            )
            n.save()
            d = Fin_ANotification(
                Login_Id=data.Login_Id,
                Title="Payment Terms Alert",
                Discription=f"Current  payment terms of {dis_name} is expiring",
            )
            d.save()
        noti = Fin_DNotification.objects.filter(
            status="New", Distributor_id=com.id
        ).order_by("-id", "-Noti_date")
        n = len(noti)

        # Calculate the date 20 days before the end date for payment term renew and 10 days before for trial period renew
        reminder_date = com.End_date - timedelta(days=20)
        current_date = date.today()
        alert_message = current_date >= reminder_date

        # Calculate the number of days between the reminder date and end date
        days_left = (com.End_date - current_date).days
        return Response(
            {
                "status": True,
                "alert_message": alert_message,
                "endDate": com.End_date,
                "days_left": days_left,
                "payment_request": payment_request,
            },
            status=status.HTTP_200_OK,
        )
    except Exception as e:
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(("GET",))
def Fin_getModules(request, id):
    try:
        data = Fin_Login_Details.objects.get(id=id)
        com = Fin_Company_Details.objects.get(Login_Id=data)
        modules = Fin_Modules_List.objects.get(Login_Id=data, status="New")
        module_request = Fin_Modules_List.objects.filter(
            company_id=com, status="pending"
        ).exists()
        serializer = ModulesListSerializer(modules)
        return Response(
            {
                "status": True,
                "module_request": module_request,
                "modules": serializer.data,
            },
            status=status.HTTP_200_OK,
        )
    except Fin_Company_Details.DoesNotExist:
        return Response(
            {"status": False, "message": "Company not found"},
            status=status.HTTP_404_NOT_FOUND,
        )
    except Exception as e:
        print(e)
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(("POST",))
def Fin_EditModules(request):
    try:
        login_id = request.data["Login_Id"]
        data = Fin_Login_Details.objects.get(id=login_id)
        com = Fin_Company_Details.objects.get(Login_Id=data.id)

        request.data["company_id"] = com.id
        request.data["status"] = "pending"

        serializer = ModulesListSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            data1 = Fin_Modules_List.objects.filter(company_id=com).update(
                update_action=1
            )
            modules = Fin_Modules_List.objects.get(id=serializer.data["id"])
            if com.Registration_Type == "self":
                noti = Fin_ANotification(
                    Login_Id=data,
                    Modules_List=modules,
                    Title="Module Updation",
                    Discription=com.Company_name + " wants to update current Modules",
                )
                noti.save()
            else:
                noti = Fin_DNotification(
                    Distributor_id=com.Distributor_id,
                    Login_Id=data,
                    Modules_List=modules,
                    Title="Module Updation",
                    Discription=com.Company_name + " wants to update current Modules",
                )
                noti.save()

            return Response(
                {"status": True, "data": serializer.data}, status=status.HTTP_200_OK
            )
        else:
            return Response(
                {"status": False, "data": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
    except Fin_Login_Details.DoesNotExist:
        return Response(
            {"status": False, "message": "Login details not found"},
            status=status.HTTP_404_NOT_FOUND,
        )
    except Fin_Company_Details.DoesNotExist:
        return Response(
            {"status": False, "message": "Company details not found"},
            status=status.HTTP_404_NOT_FOUND,
        )
    except Exception as e:
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(("GET",))
def Fin_fetchAdminNotifications(request):
    try:
        noti = Fin_ANotification.objects.filter(status="New").order_by(
            "-id", "-Noti_date"
        )
        serializer = ANotificationsSerializer(noti, many=True)
        return Response(
            {"status": True, "notifications": serializer.data},
            status=status.HTTP_200_OK,
        )
    except Exception as e:
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(("GET",))
def Fin_fetchDistributorNotifications(request, id):
    try:
        dist = Fin_Distributors_Details.objects.get(Login_Id=id)
        noti = Fin_DNotification.objects.filter(
            Distributor_id=dist, status="New"
        ).order_by("-id", "-Noti_date")
        serializer = DNotificationsSerializer(noti, many=True)
        return Response(
            {"status": True, "notifications": serializer.data},
            status=status.HTTP_200_OK,
        )
    except Exception as e:
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(("GET",))
def Fin_getAdminNotificationOverview(request, id):
    try:
        data = Fin_ANotification.objects.get(id=id)
        if data.Login_Id.User_Type == "Company":
            com = Fin_Company_Details.objects.get(Login_Id=data.Login_Id)
            modules = Fin_Modules_List.objects.get(company_id=com, status="New")
            serializer = ModulesListSerializer(modules)
            req = {
                "id": data.id,
                "user": "Company",
                "name": com.Company_name,
                "email": com.Email,
                "code": com.Company_Code,
                "contact": com.Contact,
                "username": com.Login_Id.User_name,
                "image": com.Image.url if com.Image else "",
                "endDate": com.End_date,
                "termUpdation": True if data.PaymentTerms_updation else False,
                "moduleUpdation": True if data.Modules_List else False,
                "term": (
                    str(com.Payment_Term.payment_terms_number)
                    + " "
                    + com.Payment_Term.payment_terms_value
                    if com.Payment_Term
                    else "Trial Period"
                ),
                "newTerm": (
                    str(data.PaymentTerms_updation.Payment_Term.payment_terms_number)
                    + " "
                    + data.PaymentTerms_updation.Payment_Term.payment_terms_value
                    if data.PaymentTerms_updation
                    else ""
                ),
            }
            if data.Modules_List:
                modules_pending = Fin_Modules_List.objects.filter(
                    Login_Id=data.Login_Id, status="pending"
                )
                current_modules = Fin_Modules_List.objects.filter(
                    Login_Id=data.Login_Id, status="New"
                )

                # Extract the field names related to modules
                module_fields = [
                    field.name
                    for field in Fin_Modules_List._meta.fields
                    if field.name
                    not in [
                        "id",
                        "company",
                        "status",
                        "update_action",
                        "company_id",
                        "Login_Id",
                    ]
                ]

                # Get the previous and new values for the selected modules
                previous_values = current_modules.values(*module_fields).first()
                new_values = modules_pending.values(*module_fields).first()

                # Iterate through the dictionary and replace None with 0
                for key, value in previous_values.items():
                    if value is None:
                        previous_values[key] = 0

                # Iterate through the dictionary and replace None with 0
                for key, value in new_values.items():
                    if value is None:
                        new_values[key] = 0

                # Identify added and deducted modules
                added_modules = {}
                deducted_modules = {}

                for field in module_fields:
                    if new_values[field] > previous_values[field]:
                        added_modules[field] = (
                            new_values[field] - previous_values[field]
                        )
                    elif new_values[field] < previous_values[field]:
                        deducted_modules[field] = (
                            previous_values[field] - new_values[field]
                        )

                return Response(
                    {
                        "status": True,
                        "data": req,
                        "modules": serializer.data,
                        "added_modules": added_modules,
                        "deducted_modules": deducted_modules,
                    },
                    status=status.HTTP_200_OK,
                )
            else:
                return Response(
                    {"status": True, "data": req}, status=status.HTTP_200_OK
                )
        else:
            com = Fin_Distributors_Details.objects.get(Login_Id=data.Login_Id)
            req = {
                "id": data.id,
                "user": "Distributor",
                "name": com.Login_Id.First_name + " " + com.Login_Id.Last_name,
                "email": com.Email,
                "code": com.Distributor_Code,
                "contact": com.Contact,
                "username": com.Login_Id.User_name,
                "image": com.Image.url if com.Image else "",
                "endDate": com.End_date,
                "termUpdation": True if data.PaymentTerms_updation else False,
                "moduleUpdation": False,
                "term": (
                    str(com.Payment_Term.payment_terms_number)
                    + " "
                    + com.Payment_Term.payment_terms_value
                    if com.Payment_Term
                    else "Trial Period"
                ),
                "newTerm": (
                    str(data.PaymentTerms_updation.Payment_Term.payment_terms_number)
                    + " "
                    + data.PaymentTerms_updation.Payment_Term.payment_terms_value
                    if data.PaymentTerms_updation
                    else ""
                ),
            }
            return Response({"status": True, "data": req}, status=status.HTTP_200_OK)
    except Fin_Company_Details.DoesNotExist:
        return Response(
            {"status": False, "message": "Company not found"},
            status=status.HTTP_404_NOT_FOUND,
        )
    except Fin_Distributors_Details.DoesNotExist:
        return Response(
            {"status": False, "message": "Distributor not found"},
            status=status.HTTP_404_NOT_FOUND,
        )
    except Exception as e:
        print(e)
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(("POST",))
def Fin_Module_Updation_Accept(request):
    try:
        id = request.data["id"]
        data = Fin_ANotification.objects.get(id=id)
        allmodules = Fin_Modules_List.objects.get(Login_Id=data.Login_Id, status="New")
        allmodules.delete()

        allmodules1 = Fin_Modules_List.objects.get(
            Login_Id=data.Login_Id, status="pending"
        )
        allmodules1.status = "New"
        allmodules1.save()

        data.status = "old"
        data.save()

        # notification
        Fin_CNotification.objects.create(
            Login_Id=allmodules1.Login_Id,
            Company_id=allmodules1.company_id,
            Title="Modules Updated..!",
            Discription="Your module update request is approved",
        )

        return Response({"status": True}, status=status.HTTP_200_OK)
    except Exception as e:
        print(e)
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(("DELETE",))
def Fin_Module_Updation_Reject(request):
    try:
        id = request.data["id"]
        data = Fin_ANotification.objects.get(id=id)
        allmodules = Fin_Modules_List.objects.get(
            Login_Id=data.Login_Id, status="pending"
        )
        allmodules.delete()

        data.delete()

        return Response({"status": True}, status=status.HTTP_200_OK)
    except Exception as e:
        print(e)
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(("GET",))
def Fin_getDistributorNotificationOverview(request, id):
    try:
        data = Fin_DNotification.objects.get(id=id)
        com = Fin_Company_Details.objects.get(Login_Id=data.Login_Id)
        modules = Fin_Modules_List.objects.get(company_id=com, status="New")
        serializer = ModulesListSerializer(modules)
        req = {
            "id": data.id,
            "user": "Company",
            "name": com.Company_name,
            "email": com.Email,
            "code": com.Company_Code,
            "contact": com.Contact,
            "username": com.Login_Id.User_name,
            "image": com.Image.url if com.Image else None,
            "endDate": com.End_date,
            "termUpdation": True if data.PaymentTerms_updation else False,
            "moduleUpdation": True if data.Modules_List else False,
            "term": (
                str(com.Payment_Term.payment_terms_number)
                + " "
                + com.Payment_Term.payment_terms_value
                if com.Payment_Term
                else "Trial Period"
            ),
            "newTerm": (
                str(data.PaymentTerms_updation.Payment_Term.payment_terms_number)
                + " "
                + data.PaymentTerms_updation.Payment_Term.payment_terms_value
                if data.PaymentTerms_updation
                else ""
            ),
        }
        if data.Modules_List:
            modules_pending = Fin_Modules_List.objects.filter(
                Login_Id=data.Login_Id, status="pending"
            )
            current_modules = Fin_Modules_List.objects.filter(
                Login_Id=data.Login_Id, status="New"
            )

            # Extract the field names related to modules
            module_fields = [
                field.name
                for field in Fin_Modules_List._meta.fields
                if field.name
                not in [
                    "id",
                    "company",
                    "status",
                    "update_action",
                    "company_id",
                    "Login_Id",
                ]
            ]

            # Get the previous and new values for the selected modules
            previous_values = current_modules.values(*module_fields).first()
            new_values = modules_pending.values(*module_fields).first()

            # Iterate through the dictionary and replace None with 0
            for key, value in previous_values.items():
                if value is None:
                    previous_values[key] = 0

            # Iterate through the dictionary and replace None with 0
            for key, value in new_values.items():
                if value is None:
                    new_values[key] = 0

            # Identify added and deducted modules
            added_modules = {}
            deducted_modules = {}

            for field in module_fields:
                if new_values[field] > previous_values[field]:
                    added_modules[field] = new_values[field] - previous_values[field]
                elif new_values[field] < previous_values[field]:
                    deducted_modules[field] = previous_values[field] - new_values[field]

            return Response(
                {
                    "status": True,
                    "data": req,
                    "modules": serializer.data,
                    "added_modules": added_modules,
                    "deducted_modules": deducted_modules,
                },
                status=status.HTTP_200_OK,
            )
        else:
            return Response({"status": True, "data": req}, status=status.HTTP_200_OK)
    except Fin_Company_Details.DoesNotExist:
        return Response(
            {"status": False, "message": "Company not found"},
            status=status.HTTP_404_NOT_FOUND,
        )
    except Fin_Distributors_Details.DoesNotExist:
        return Response(
            {"status": False, "message": "Distributor not found"},
            status=status.HTTP_404_NOT_FOUND,
        )
    except Exception as e:
        print(e)
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(("POST",))
def Fin_DModule_Updation_Accept(request):
    try:
        id = request.data["id"]
        data = Fin_DNotification.objects.get(id=id)
        allmodules = Fin_Modules_List.objects.get(Login_Id=data.Login_Id, status="New")
        allmodules.delete()

        allmodules1 = Fin_Modules_List.objects.get(
            Login_Id=data.Login_Id, status="pending"
        )
        allmodules1.status = "New"
        allmodules1.save()

        data.status = "old"
        data.save()

        # notification
        Fin_CNotification.objects.create(
            Login_Id=allmodules1.Login_Id,
            Company_id=allmodules1.company_id,
            Title="Modules Updated..!",
            Discription="Your module update request is approved",
        )

        return Response({"status": True}, status=status.HTTP_200_OK)
    except Exception as e:
        print(e)
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(("DELETE",))
def Fin_DModule_Updation_Reject(request):
    try:
        id = request.data["id"]
        data = Fin_DNotification.objects.get(id=id)
        allmodules = Fin_Modules_List.objects.get(
            Login_Id=data.Login_Id, status="pending"
        )
        allmodules.delete()

        data.delete()

        return Response({"status": True}, status=status.HTTP_200_OK)
    except Exception as e:
        print(e)
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


# ITEMS
@api_view(("GET",))
def Fin_getCompanyItemUnits(request, id):
    try:
        data = Fin_Login_Details.objects.get(id=id)
        if data.User_Type == 'Company':
            cmp = Fin_Company_Details.objects.get(Login_Id=id)
        else:
            cmp = Fin_Staff_Details.objects.get(Login_Id = id).company_id
        units = Fin_Units.objects.filter(Company=cmp)
        serializer = ItemUnitSerializer(units, many=True)
        return Response(
            {"status": True, "units": serializer.data}, status=status.HTTP_200_OK
        )
    except Exception as e:
        print(e)
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(("GET",))
def Fin_getCompanyAccounts(request, id):
    try:
        data = Fin_Login_Details.objects.get(id=id)
        if data.User_Type == 'Company':
            cmp = Fin_Company_Details.objects.get(Login_Id=id)
        else:
            cmp = Fin_Staff_Details.objects.get(Login_Id = id).company_id
        acc = Fin_Chart_Of_Account.objects.filter(
            Q(account_type="Expense")
            | Q(account_type="Other Expense")
            | Q(account_type="Cost Of Goods Sold"),
            Company=cmp,
        ).order_by("account_name")
        serializer = AccountsSerializer(acc, many=True)
        return Response(
            {"status": True, "accounts": serializer.data}, status=status.HTTP_200_OK
        )
    except Exception as e:
        print(e)
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(("POST",))
def Fin_createNewItem(request):
    try:
        s_id = request.data["Id"]
        data = Fin_Login_Details.objects.get(id=s_id)
        if data.User_Type == "Company":
            com = Fin_Company_Details.objects.get(Login_Id=s_id)
        else:
            com = Fin_Staff_Details.objects.get(Login_Id=s_id).company_id

        createdDate = date.today()
        if request.data["item_type"] == "Goods":
            request.data["sac"] = None
        else:
            request.data["hsn"] = None
        request.data["intra_state_tax"] = (
            0
            if request.data["tax_reference"] == "non taxable"
            else request.data["intra_state_tax"]
        )
        request.data["inter_state_tax"] = (
            0
            if request.data["tax_reference"] == "non taxable"
            else request.data["inter_state_tax"]
        )
        request.data["sales_account"] = (
            None
            if request.data["sales_account"] == ""
            else request.data["sales_account"]
        )
        request.data["purchase_account"] = (
            None
            if request.data["purchase_account"] == ""
            else request.data["purchase_account"]
        )
        request.data["created_date"] = createdDate

        # save item and transaction if item or hsn doesn't exists already
        if Fin_Items.objects.filter(
            Company=com, name__iexact=request.data["name"]
        ).exists():
            return Response({"status": False, "message": "Item Name already exists"})
        elif Fin_Items.objects.filter(
            Q(Company=com) & (Q(hsn__iexact=request.data["hsn"]) & Q(hsn__isnull=False))
        ).exists():
            return Response({"status": False, "message": "HSN already exists"})
        elif Fin_Items.objects.filter(
            Q(Company=com) & (Q(sac__iexact=request.data["sac"]) & Q(sac__isnull=False))
        ).exists():
            return Response({"status": False, "message": "SAC already exists"})
        else:
            request.data["Company"] = com.id
            request.data["LoginDetails"] = com.Login_Id.id
            serializer = ItemSerializer(data=request.data)
            if serializer.is_valid():
                # save transaction
                serializer.save()

                Fin_Items_Transaction_History.objects.create(
                    Company=com,
                    LoginDetails=data,
                    item=Fin_Items.objects.get(id=serializer.data["id"]),
                    action="Created",
                )

                return Response(
                    {"status": True, "data": serializer.data}, status=status.HTTP_200_OK
                )
            else:
                return Response(
                    {"status": False, "data": serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST,
                )
    except Exception as e:
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

@api_view(("POST",))
def Fin_createNewUnit(request):
    try:
        s_id = request.data["Id"]
        data = Fin_Login_Details.objects.get(id=s_id)
        if data.User_Type == "Company":
            com = Fin_Company_Details.objects.get(Login_Id=s_id)
        else:
            com = Fin_Staff_Details.objects.get(Login_Id=s_id).company_id
        request.data["Company"] = com.id
        serializer = ItemUnitSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"status": True, "data": serializer.data},
                status=status.HTTP_201_CREATED,
            )
        else:
            return Response(
                {"status": False, "data": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
    except Exception as e:
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(("GET",))
def Fin_fetchItems(request, id):
    try:
        data = Fin_Login_Details.objects.get(id=id)
        if data.User_Type == "Company":
            com = Fin_Company_Details.objects.get(Login_Id=id)
        else:
            com = Fin_Staff_Details.objects.get(Login_Id=id).company_id

        items = Fin_Items.objects.filter(Company=com)
        serializer = ItemSerializer(items, many=True)
        return Response(
            {"status": True, "items": serializer.data}, status=status.HTTP_200_OK
        )
    except Exception as e:
        print(e)
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(("GET",))
def Fin_fetchItemDetails(request, id):
    try:
        item = Fin_Items.objects.get(id=id)
        hist = Fin_Items_Transaction_History.objects.filter(item=item).last()
        his = None
        if hist:
            his = {
                "action": hist.action,
                "date": hist.date,
                "doneBy": hist.LoginDetails.First_name
                + " "
                + hist.LoginDetails.Last_name,
            }
        cmt = Fin_Items_Comments.objects.filter(item=item)
        itemSerializer = ItemSerializer(item)
        commentsSerializer = ItemCommentsSerializer(cmt, many=True)
        return Response(
            {
                "status": True,
                "item": itemSerializer.data,
                "history": his,
                "comments": commentsSerializer.data,
            },
            status=status.HTTP_200_OK,
        )
    except Exception as e:
        print(e)
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(("GET",))
def Fin_fetchItemHistory(request, id):
    try:
        item = Fin_Items.objects.get(id=id)
        hist = Fin_Items_Transaction_History.objects.filter(item=item)
        his = []
        if hist:
            for i in hist:
                h = {
                    "action": i.action,
                    "date": i.date,
                    "name": i.LoginDetails.First_name + " " + i.LoginDetails.Last_name,
                }
                his.append(h)
        itemSerializer = ItemSerializer(item)
        return Response(
            {"status": True, "item": itemSerializer.data, "history": his},
            status=status.HTTP_200_OK,
        )
    except Exception as e:
        print(e)
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(("DELETE",))
def Fin_deleteItem(request, id):
    try:
        item = Fin_Items.objects.get(id=id)
        item.delete()
        return Response({"status": True}, status=status.HTTP_200_OK)
    except Exception as e:
        print(e)
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(("DELETE",))
def Fin_deleteItemComment(request, id):
    try:
        cmt = Fin_Items_Comments.objects.get(id=id)
        cmt.delete()
        return Response({"status": True}, status=status.HTTP_200_OK)
    except Exception as e:
        print(e)
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(("POST",))
def Fin_changeItemStatus(request):
    try:
        itemId = request.data["id"]
        data = Fin_Items.objects.get(id=itemId)
        data.status = request.data["status"]
        data.save()
        return Response({"status": True}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(("POST",))
def Fin_addItemComment(request):
    try:
        id = request.data["Id"]
        data = Fin_Login_Details.objects.get(id=id)
        if data.User_Type == "Company":
            com = Fin_Company_Details.objects.get(Login_Id=id)
        else:
            com = Fin_Staff_Details.objects.get(Login_Id=id).company_id

        request.data["Company"] = com.id
        serializer = ItemCommentsSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"status": True, "data": serializer.data}, status=status.HTTP_200_OK
            )
        else:
            return Response(
                {"status": False, "data": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
    except Exception as e:
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(("GET",))
def Fin_itemTransactionPdf(request, itemId, id):
    try:
        data = Fin_Login_Details.objects.get(id=id)
        if data.User_Type == "Company":
            com = Fin_Company_Details.objects.get(Login_Id=id)
        else:
            com = Fin_Staff_Details.objects.get(Login_Id=id).company_id

        item = Fin_Items.objects.get(id=itemId)
        stock = int(item.current_stock)
        rate = float(item.stock_unit_rate)
        stockValue = float(stock * rate)

        transactions = []

        context = {"item": item, "stockValue": stockValue, "transactions": transactions}

        template_path = "company/Fin_Item_Transaction_Pdf.html"
        fname = "Item_transactions_" + item.name
        # return render(request, 'company/Fin_Item_Transaction_Pdf.html',context)
        # Create a Django response object, and specify content_type as pdftemp_
        response = HttpResponse(content_type="application/pdf")
        response["Content-Disposition"] = f"attachment; filename = {fname}.pdf"
        # find the template and render it.
        template = get_template(template_path)
        html = template.render(context)

        # create a pdf
        pisa_status = pisa.CreatePDF(html, dest=response)
        # if error then show some funny view
        if pisa_status.err:
            return HttpResponse("We had some errors <pre>" + html + "</pre>")
        return response
    except Exception as e:
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(("POST",))
def Fin_shareItemTransactionsToEmail(request):
    try:
        id = request.data["Id"]
        data = Fin_Login_Details.objects.get(id=id)
        if data.User_Type == "Company":
            com = Fin_Company_Details.objects.get(Login_Id=id)
        else:
            com = Fin_Staff_Details.objects.get(Login_Id=id).company_id

        itemId = request.data["itemId"]
        item = Fin_Items.objects.get(id=itemId)
        emails_string = request.data["email_ids"]

        # Split the string by commas and remove any leading or trailing whitespace
        emails_list = [email.strip() for email in emails_string.split(",")]
        email_message = request.data["email_message"]
        # print(emails_list)

        stock = int(item.current_stock)
        rate = float(item.stock_unit_rate)
        stockValue = float(stock * rate)

        transactions = []

        context = {"item": item, "stockValue": stockValue, "transactions": transactions}
        template_path = "company/Fin_Item_Transaction_Pdf.html"
        template = get_template(template_path)

        html = template.render(context)
        result = BytesIO()
        pdf = pisa.pisaDocument(BytesIO(html.encode("ISO-8859-1")), result)
        pdf = result.getvalue()
        filename = f"Item_transactions-{item.name}.pdf"
        subject = f"Item_transactions_{item.name}"
        email = EmailMessage(
            subject,
            f"Hi,\nPlease find the attached Transaction details - ITEM-{item.name}. \n{email_message}\n\n--\nRegards,\n{com.Company_name}\n{com.Address}\n{com.State} - {com.Country}\n{com.Contact}",
            from_email=settings.EMAIL_HOST_USER,
            to=emails_list,
        )
        email.attach(filename, pdf, "application/pdf")
        email.send(fail_silently=False)

        return Response({"status": True}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(("GET",))
def Fin_checkAccounts(request):
    try:
        s_id = request.GET["Id"]
        data = Fin_Login_Details.objects.get(id=s_id)
        if data.User_Type == "Company":
            com = Fin_Company_Details.objects.get(Login_Id=s_id)
        else:
            com = Fin_Staff_Details.objects.get(Login_Id=s_id).company_id

        if Fin_Chart_Of_Account.objects.filter(
            Company=com, account_type=request.GET["type"]
        ).exists():
            list = []
            account_objects = Fin_Chart_Of_Account.objects.filter(
                Company=com, account_type=request.GET["type"]
            )

            for account in account_objects:
                accounts = {
                    "name": account.account_name,
                }
                list.append(accounts)

            return Response(
                {"status": True, "accounts": list}, status=status.HTTP_200_OK
            )
        else:
            return Response({"status": False})
    except Exception as e:
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(("POST",))
def Fin_createNewAccountFromItems(request):
    try:
        s_id = request.data["Id"]
        data = Fin_Login_Details.objects.get(id=s_id)
        if data.User_Type == "Company":
            com = Fin_Company_Details.objects.get(Login_Id=s_id)
        else:
            com = Fin_Staff_Details.objects.get(Login_Id=s_id).company_id

        createdDate = date.today()
        request.data["Company"] = com.id
        request.data["LoginDetails"] = com.Login_Id.id
        request.data["parent_account"] = (
            request.data["parent_account"]
            if request.data["sub_account"] == True
            else None
        )
        request.data["balance"] = 0.0
        request.data["balance_type"] = None
        request.data["credit_card_no"] = None
        request.data["bank_account_no"] = None
        request.data["date"] = createdDate
        request.data["create_status"] = "added"
        request.data["status"] = "active"

        # save account and transaction if account doesn't exists already
        if Fin_Chart_Of_Account.objects.filter(
            Company=com, account_name__iexact=request.data["account_name"]
        ).exists():
            return Response(
                {"status": False, "message": "Account Name already exists."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        else:
            serializer = AccountsSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                # save transaction

                Fin_ChartOfAccount_History.objects.create(
                    Company=com,
                    LoginDetails=data,
                    account=Fin_Chart_Of_Account.objects.get(id=serializer.data["id"]),
                    action="Created",
                )
                return Response(
                    {"status": True, "data": serializer.data}, status=status.HTTP_200_OK
                )
            else:
                return Response(
                    {"status": False, "data": serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST,
                )
    except Exception as e:
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
    
@api_view(("GET",))
def minStock(request, id):
    try:
        s_id = id
        data = Fin_Login_Details.objects.get(id=s_id)
        if data.User_Type != 'Distributor':
            if data.User_Type == "Company":
                com = Fin_Company_Details.objects.get(Login_Id = s_id)
            elif data.User_Type == 'Staff':
                com = Fin_Staff_Details.objects.get(Login_Id = s_id).company_id
            
            itemsAvailable = Fin_Items.objects.filter(Company = com)

            if Fin_CNotification.objects.filter(Company_id=com, Item__isnull=False).exists():
                alertItems = Fin_CNotification.objects.filter(Company_id=com, Item__isnull=False)
                for item in alertItems:
                    stockItem = Fin_Items.objects.get(id = item.Item.id)
                    if stockItem.current_stock > stockItem.min_stock:
                        item.status = 'Old'
                        item.save()
                    else:
                        item.status = 'New'
                        item.save()
                
                for itm in itemsAvailable:
                    if not Fin_CNotification.objects.filter(Item = itm).exists():
                        if itm.min_stock > 0 and itm.current_stock < itm.min_stock:
                            Fin_CNotification.objects.create(Company_id = com, Login_Id = data, Item = itm, Title = 'Stock Alert.!!', Discription = f'{itm.name} is below the minimum stock threshold..')

            else:
                for itm in itemsAvailable:
                    if itm.min_stock > 0 and itm.current_stock < itm.min_stock:
                        Fin_CNotification.objects.create(Company_id = com, Login_Id = data, Item = itm, Title = 'Stock Alert.!!', Discription = f'{itm.name} is below the minimum stock threshold..')
            
            stockLow = Fin_CNotification.objects.filter(Company_id = com, Item__isnull=False, status = 'New')
            nCount = Fin_CNotification.objects.filter(Company_id = com, status = 'New')
            if stockLow:
                serializer = CNotificationsSerializer(stockLow, many=True)
                return Response(
                    {"status": True, "minStockAlerts": serializer.data, 'count':len(nCount)},
                    status=status.HTTP_200_OK,
                )
            else:
                return Response(
                    {"status": True, "minStockAlerts": None, 'count':len(nCount)},
                    status=status.HTTP_200_OK,
                )
        else:
            return Response({"status": False},status=status.HTTP_200_OK)
    except Exception as e:
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

@api_view(("PUT",))
def Fin_updateItem(request):
    try:
        s_id = request.data["Id"]
        data = Fin_Login_Details.objects.get(id=s_id)
        if data.User_Type == "Company":
            com = Fin_Company_Details.objects.get(Login_Id=s_id)
        else:
            com = Fin_Staff_Details.objects.get(Login_Id=s_id).company_id
        
        item = Fin_Items.objects.get(id=request.data['itemId'])
        if request.data["item_type"] == "Goods":
            request.data["sac"] = None
        else:
            request.data["hsn"] = None
        request.data["intra_state_tax"] = (
            0
            if request.data["tax_reference"] == "non taxable"
            else request.data["intra_state_tax"]
        )
        request.data["inter_state_tax"] = (
            0
            if request.data["tax_reference"] == "non taxable"
            else request.data["inter_state_tax"]
        )
        request.data["sales_account"] = (
            None
            if request.data["sales_account"] == ""
            else request.data["sales_account"]
        )
        request.data["purchase_account"] = (
            None
            if request.data["purchase_account"] == ""
            else request.data["purchase_account"]
        )

        #save item and transaction if item or hsn doesn't exists already
        name = request.data['name']
        hsn = request.data['hsn']
        sac = request.data['sac']
        
        if item.name != name and Fin_Items.objects.filter(Company=com, name__iexact=name).exists():
            return Response({'status':False, 'message':'Item Name exists'}, status=status.HTTP_400_BAD_REQUEST)
        
        if item.hsn and hsn != None:
            if int(item.hsn) != int(hsn) and Fin_Items.objects.filter(Company = com, hsn__iexact=hsn).exists():
                return Response({'status':False, 'message':'HSN Code Exists'}, status=status.HTTP_400_BAD_REQUEST)
        
        if item.sac and sac != None:
            if int(item.sac) != int(sac) and Fin_Items.objects.filter(Company = com, sac__iexact=sac).exists():
                return Response({'status':False, 'message':'SAC Code Exists'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = ItemSerializer(item,data=request.data)
        if serializer.is_valid():
            stock = item.opening_stock if request.data['opening_stock'] == "" else request.data['opening_stock']
            oldOpen = int(item.opening_stock)
            newOpen = int(stock)
            diff = abs(oldOpen - newOpen)
            if item.opening_stock != int(stock) and oldOpen > newOpen:
                request.data['current_stock'] = item.current_stock - diff
            elif item.opening_stock != int(stock) and oldOpen < newOpen:
                request.data['current_stock'] = item.current_stock + diff

            # save transaction
            serializer.save()

            Fin_Items_Transaction_History.objects.create(
                Company=com,
                LoginDetails=data,
                item=Fin_Items.objects.get(id=serializer.data["id"]),
                action="Edited",
            )

            return Response(
                {"status": True, "data": serializer.data}, status=status.HTTP_200_OK
            )
        else:
            return Response(
                {"status": False, "data": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
    except Exception as e:
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


# Customers
@api_view(("GET",))
def Fin_fetchCustomers(request, id):
    try:
        data = Fin_Login_Details.objects.get(id=id)
        if data.User_Type == "Company":
            com = Fin_Company_Details.objects.get(Login_Id=id)
        else:
            com = Fin_Staff_Details.objects.get(Login_Id=id).company_id

        customers = Fin_Customers.objects.filter(Company=com)
        serializer = CustomerSerializer(customers, many=True)
        return Response(
            {"status": True, "customers": serializer.data}, status=status.HTTP_200_OK
        )
    except Exception as e:
        print(e)
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

@api_view(("GET",))
def Fin_getCompanyPaymentTerms(request, id):
    try:
        data = Fin_Login_Details.objects.get(id=id)
        if data.User_Type == 'Company':
            cmp = Fin_Company_Details.objects.get(Login_Id=id)
        else:
            cmp = Fin_Staff_Details.objects.get(Login_Id = id).company_id
        pTerms = Fin_Company_Payment_Terms.objects.filter(Company=cmp)
        serializer = CompanyPaymentTermsSerializer(pTerms, many=True)
        return Response(
            {"status": True, "terms": serializer.data}, status=status.HTTP_200_OK
        )
    except Exception as e:
        print(e)
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
    
@api_view(("GET",))
def Fin_getSalesPriceLists(request, id):
    try:
        data = Fin_Login_Details.objects.get(id=id)
        if data.User_Type == 'Company':
            cmp = Fin_Company_Details.objects.get(Login_Id=id)
        else:
            cmp = Fin_Staff_Details.objects.get(Login_Id = id).company_id
        lists = Fin_Price_List.objects.filter(Company=cmp)
        serializer = PriceListSerializer(lists, many=True)
        return Response(
            {"status": True, "salesPriceLists": serializer.data}, status=status.HTTP_200_OK
        )
    except Exception as e:
        print(e)
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

@api_view(("POST",))
def Fin_createNewCompanyPaymentTerm(request):
    try:
        s_id = request.data["Id"]
        data = Fin_Login_Details.objects.get(id=s_id)
        if data.User_Type == "Company":
            com = Fin_Company_Details.objects.get(Login_Id=s_id)
        else:
            com = Fin_Staff_Details.objects.get(Login_Id=s_id).company_id
        request.data["Company"] = com.id
        if not Fin_Company_Payment_Terms.objects.filter(Company = com, term_name__iexact = request.data['term_name']).exists():
            serializer = CompanyPaymentTermsSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(
                    {"status": True, "data": serializer.data},
                    status=status.HTTP_201_CREATED,
                )
            else:
                return Response(
                    {"status": False, "data": serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        else:
            return Response(
                {"status": False, "message": 'Term name exists'},
                status=status.HTTP_400_BAD_REQUEST,
            )
    except Exception as e:
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

@api_view(("GET",))
def Fin_checkGstIn(request):
    try:
        data = Fin_Login_Details.objects.get(id=request.GET['Id'])
        if data.User_Type == 'Company':
            cmp = Fin_Company_Details.objects.get(Login_Id=data)
        else:
            cmp = Fin_Staff_Details.objects.get(Login_Id = data).company_id
        
        gstIn = request.GET['gstin']
        if Fin_Customers.objects.filter(Company = cmp, gstin__iexact = gstIn).exists():
            return Response({'is_exist':True, 'message':f'{gstIn} already exists, Try another.!'})
        else:
            return Response({'is_exist':False})
    except Exception as e:
        print(e)
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

@api_view(("GET",))
def Fin_checkPan(request):
    try:
        data = Fin_Login_Details.objects.get(id=request.GET['Id'])
        if data.User_Type == 'Company':
            cmp = Fin_Company_Details.objects.get(Login_Id=data)
        else:
            cmp = Fin_Staff_Details.objects.get(Login_Id = data).company_id
        
        pan = request.GET['pan']
        if Fin_Customers.objects.filter(Company = cmp, pan_no__iexact = pan).exists():
            return Response({'is_exist':True, 'message':f'{pan} already exists, Try another.!'})
        else:
            return Response({'is_exist':False})
    except Exception as e:
        print(e)
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

@api_view(("GET",))
def Fin_checkPhone(request):
    try:
        data = Fin_Login_Details.objects.get(id=request.GET['Id'])
        if data.User_Type == 'Company':
            cmp = Fin_Company_Details.objects.get(Login_Id=data)
        else:
            cmp = Fin_Staff_Details.objects.get(Login_Id = data).company_id
        
        phn = request.GET['phone']
        if Fin_Customers.objects.filter(Company = cmp, mobile__iexact = phn).exists():
            return Response({'is_exist':True, 'message':f'{phn} already exists, Try another.!'})
        else:
            return Response({'is_exist':False})
    except Exception as e:
        print(e)
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

@api_view(("GET",))
def Fin_checkEmail(request):
    try:
        data = Fin_Login_Details.objects.get(id=request.GET['Id'])
        if data.User_Type == 'Company':
            cmp = Fin_Company_Details.objects.get(Login_Id=data)
        else:
            cmp = Fin_Staff_Details.objects.get(Login_Id = data).company_id
        
        eml = request.GET['email']
        if Fin_Customers.objects.filter(Company = cmp, email__iexact = eml).exists():
            return Response({'is_exist':True, 'message':f'{eml} already exists, Try another.!'})
        else:
            return Response({'is_exist':False})
    except Exception as e:
        print(e)
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

@api_view(("GET",))
def Fin_checkCustomerName(request):
    try:
        data = Fin_Login_Details.objects.get(id=request.GET['Id'])
        if data.User_Type == 'Company':
            cmp = Fin_Company_Details.objects.get(Login_Id=data)
        else:
            cmp = Fin_Staff_Details.objects.get(Login_Id = data).company_id
        
        fName = request.GET['fName']
        lName = request.GET['lName']

        if Fin_Customers.objects.filter(Company = cmp, first_name__iexact = fName, last_name__iexact = lName).exists():
            msg = f'{fName} {lName} already exists, Try another.!'
            return Response({'is_exist':True, 'message':msg})
        else:
            return Response({'is_exist':False})
    except Exception as e:
        print(e)
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(("POST",))
def Fin_createNewCustomer(request):
    try:
        s_id = request.data["Id"]
        data = Fin_Login_Details.objects.get(id=s_id)
        if data.User_Type == "Company":
            com = Fin_Company_Details.objects.get(Login_Id=s_id)
        else:
            com = Fin_Staff_Details.objects.get(Login_Id=s_id).company_id

        fName = request.data['first_name']
        lName = request.data['last_name']
        gstIn = request.data['gstin']
        pan = request.data['pan_no']
        email = request.data['email']
        phn = request.data['mobile']

        if Fin_Customers.objects.filter(Company = com, first_name__iexact = fName, last_name__iexact = lName).exists():
            return Response({"status": False, "message": f"Customer `{fName} {lName}` already exists, try another!"}, status=status.HTTP_400_BAD_REQUEST)
        elif Fin_Customers.objects.filter(Company = com, gstin__iexact = gstIn).exists():
            return Response({"status": False, "message": f"GSTIN `{gstIn}` already exists, try another!"}, status=status.HTTP_400_BAD_REQUEST)
        elif Fin_Customers.objects.filter(Company = com, pan_no__iexact = pan).exists():
            return Response({"status": False, "message": f"PAN No `{pan}` already exists, try another!"}, status=status.HTTP_400_BAD_REQUEST)
        elif Fin_Customers.objects.filter(Company = com, mobile__iexact = phn).exists():
            return Response({"status": False, "message": f"Phone Number `{phn}` already exists, try another!"}, status=status.HTTP_400_BAD_REQUEST)
        elif Fin_Customers.objects.filter(Company = com, email__iexact = email).exists():
            return Response({"status": False, "message": f"Email `{email}` already exists, try another!"}, status=status.HTTP_400_BAD_REQUEST)
        else:
            request.data["Company"] = com.id
            request.data["LoginDetails"] = com.Login_Id.id
            request.data['gstin'] = None if request.data['gst_type'] == "Unregistered Business" or request.data['gst_type'] == 'Overseas' or request.data['gst_type'] == 'Consumer' else request.data['gstin']
            request.data['price_list'] = None if request.data['price_list'] ==  "" else request.data['price_list']
            request.data['payment_terms'] = None if request.data['payment_terms'] == "" else request.data['payment_terms']
            request.data['opening_balance'] = 0 if request.data['opening_balance'] == "" else float(request.data['opening_balance'])
            request.data['current_balance'] = 0 if request.data['opening_balance'] == "" else float(request.data['opening_balance'])
            request.data['credit_limit'] = 0 if request.data['credit_limit'] == "" else float(request.data['credit_limit'])

            serializer = CustomerSerializer(data=request.data)
            if serializer.is_valid():
                # save transaction
                serializer.save()

                Fin_Customers_History.objects.create(
                    Company = com,
                    LoginDetails = data,
                    customer = Fin_Customers.objects.get(id=serializer.data['id']),
                    action = 'Created'
                )

                return Response(
                    {"status": True, "data": serializer.data}, status=status.HTTP_200_OK
                )
            else:
                return Response(
                    {"status": False, "data": serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST,
                )
    except Exception as e:
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

@api_view(("POST",))
def Fin_addCustomerComment(request):
    try:
        id = request.data["Id"]
        data = Fin_Login_Details.objects.get(id=id)
        if data.User_Type == "Company":
            com = Fin_Company_Details.objects.get(Login_Id=id)
        else:
            com = Fin_Staff_Details.objects.get(Login_Id=id).company_id

        request.data["Company"] = com.id
        serializer = CustomerCommentsSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"status": True, "data": serializer.data}, status=status.HTTP_200_OK
            )
        else:
            return Response(
                {"status": False, "data": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
    except Exception as e:
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

@api_view(("DELETE",))
def Fin_deleteCustomerComment(request, id):
    try:
        cmt = Fin_Customers_Comments.objects.get(id=id)
        cmt.delete()
        return Response({"status": True}, status=status.HTTP_200_OK)
    except Exception as e:
        print(e)
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
    
@api_view(("GET",))
def Fin_fetchCustomerDetails(request, id):
    try:
        cust = Fin_Customers.objects.get(id=id)
        hist = Fin_Customers_History.objects.filter(customer=cust).last()
        his = None
        if hist:
            his = {
                "action": hist.action,
                "date": hist.date,
                "doneBy": hist.LoginDetails.First_name
                + " "
                + hist.LoginDetails.Last_name,
            }
        cmt = Fin_Customers_Comments.objects.filter(customer=cust)
        customerSerializer = CustomerSerializer(cust)
        commentsSerializer = CustomerCommentsSerializer(cmt, many=True)
        extObj = {
            'paymentTerms': cust.payment_terms.term_name if cust.payment_terms else 'Nill',
            'priceList': cust.price_list.name if cust.price_list else 'Nill'
        }
        return Response(
            {
                "status": True,
                "customer": customerSerializer.data,
                "history": his,
                "comments": commentsSerializer.data,
                "extraDetails": extObj
            },
            status=status.HTTP_200_OK,
        )
    except Exception as e:
        print(e)
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

@api_view(("POST",))
def Fin_changeCustomerStatus(request):
    try:
        custId = request.data["id"]
        data = Fin_Customers.objects.get(id=custId)
        data.status = request.data["status"]
        data.save()
        return Response({"status": True}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

@api_view(("GET",))
def Fin_fetchCustomerHistory(request, id):
    try:
        cust = Fin_Customers.objects.get(id=id)
        hist = Fin_Customers_History.objects.filter(customer=cust)
        his = []
        if hist:
            for i in hist:
                h = {
                    "action": i.action,
                    "date": i.date,
                    "name": i.LoginDetails.First_name + " " + i.LoginDetails.Last_name,
                }
                his.append(h)
        customerSerializer = CustomerSerializer(cust)
        return Response(
            {"status": True, "customer": customerSerializer.data, "history": his},
            status=status.HTTP_200_OK,
        )
    except Exception as e:
        print(e)
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

@api_view(("DELETE",))
def Fin_deleteCustomer(request, id):
    try:
        cust = Fin_Customers.objects.get(id=id)
        cust.delete()
        return Response({"status": True}, status=status.HTTP_200_OK)
    except Exception as e:
        print(e)
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

@api_view(("GET",))
def Fin_customerTransactionPdf(request):
    try:
        id = request.GET['Id']
        custId = request.GET['c_id']

        data = Fin_Login_Details.objects.get(id=id)
        if data.User_Type == "Company":
            com = Fin_Company_Details.objects.get(Login_Id=id)
        else:
            com = Fin_Staff_Details.objects.get(Login_Id=id).company_id

        cust = Fin_Customers.objects.get(id=custId)
        context = {"customer": cust}

        template_path = "company/Fin_Customer_Transaction_Pdf.html"
        fname = "Customer_transaction_" + cust.first_name
        # Create a Django response object, and specify content_type as pdftemp_
        response = HttpResponse(content_type="application/pdf")
        response["Content-Disposition"] = f"attachment; filename = {fname}.pdf"
        # find the template and render it.
        template = get_template(template_path)
        html = template.render(context)

        # create a pdf
        pisa_status = pisa.CreatePDF(html, dest=response)
        # if error then show some funny view
        if pisa_status.err:
            return HttpResponse("We had some errors <pre>" + html + "</pre>")
        return response
    except Exception as e:
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

@api_view(("POST",))
def Fin_shareCustomerTransactionsToEmail(request):
    try:
        id = request.data["Id"]
        data = Fin_Login_Details.objects.get(id=id)
        if data.User_Type == "Company":
            com = Fin_Company_Details.objects.get(Login_Id=id)
        else:
            com = Fin_Staff_Details.objects.get(Login_Id=id).company_id

        custId = request.data["c_id"]
        cust = Fin_Customers.objects.get(id=custId)
        emails_string = request.data["email_ids"]

        # Split the string by commas and remove any leading or trailing whitespace
        emails_list = [email.strip() for email in emails_string.split(",")]
        email_message = request.data["email_message"]
        # print(emails_list)

        context = {"customer": cust}
        template_path = "company/Fin_Customer_Transaction_Pdf.html"
        template = get_template(template_path)

        html = template.render(context)
        result = BytesIO()
        pdf = pisa.pisaDocument(BytesIO(html.encode("ISO-8859-1")), result)
        pdf = result.getvalue()
        filename = f"Customer_transactions-{cust.first_name}.pdf"
        subject = f"Customer_transactions_{cust.first_name}"
        email = EmailMessage(
            subject,
            f"Hi,\nPlease find the attached Transaction details - Customer-{cust.first_name}. \n{email_message}\n\n--\nRegards,\n{com.Company_name}\n{com.Address}\n{com.State} - {com.Country}\n{com.Contact}",
            from_email=settings.EMAIL_HOST_USER,
            to=emails_list,
        )
        email.attach(filename, pdf, "application/pdf")
        email.send(fail_silently=False)

        return Response({"status": True}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
    
@api_view(("PUT",))
def Fin_updateCustomer(request):
    try:
        s_id = request.data["Id"]
        data = Fin_Login_Details.objects.get(id=s_id)
        if data.User_Type == "Company":
            com = Fin_Company_Details.objects.get(Login_Id=s_id)
        else:
            com = Fin_Staff_Details.objects.get(Login_Id=s_id).company_id

        cust = Fin_Customers.objects.get(id=request.data['c_id'])
        fName = request.data['first_name']
        lName = request.data['last_name']
        gstIn = request.data['gstin']
        pan = request.data['pan_no']
        email = request.data['email']
        phn = request.data['mobile']

        if cust.first_name != fName and cust.last_name != lName and Fin_Customers.objects.filter(Company = com, first_name__iexact = fName, last_name__iexact = lName).exists():
            return Response({"status": False, "message": f"Customer `{fName} {lName}` already exists, try another!"}, status=status.HTTP_400_BAD_REQUEST)
        elif cust.gstin != gstIn and Fin_Customers.objects.filter(Company = com, gstin__iexact = gstIn).exists():
            return Response({"status": False, "message": f"GSTIN `{gstIn}` already exists, try another!"}, status=status.HTTP_400_BAD_REQUEST)
        elif cust.pan_no != pan and Fin_Customers.objects.filter(Company = com, pan_no__iexact = pan).exists():
            return Response({"status": False, "message": f"PAN No `{pan}` already exists, try another!"}, status=status.HTTP_400_BAD_REQUEST)
        elif cust.mobile != phn and Fin_Customers.objects.filter(Company = com, mobile__iexact = phn).exists():
            return Response({"status": False, "message": f"Phone Number `{phn}` already exists, try another!"}, status=status.HTTP_400_BAD_REQUEST)
        elif cust.email != email and Fin_Customers.objects.filter(Company = com, email__iexact = email).exists():
            return Response({"status": False, "message": f"Email `{email}` already exists, try another!"}, status=status.HTTP_400_BAD_REQUEST)
        else:
            request.data['gstin'] = None if request.data['gst_type'] == "Unregistered Business" or request.data['gst_type'] == 'Overseas' or request.data['gst_type'] == 'Consumer' else request.data['gstin']
            request.data['price_list'] = None if request.data['price_list'] ==  "" else request.data['price_list']
            request.data['payment_terms'] = None if request.data['payment_terms'] == "" else request.data['payment_terms']
            request.data['opening_balance'] = 0 if request.data['opening_balance'] == "" else float(request.data['opening_balance'])
            request.data['current_balance'] = 0 if request.data['opening_balance'] == "" else float(request.data['opening_balance'])
            request.data['credit_limit'] = 0 if request.data['credit_limit'] == "" else float(request.data['credit_limit'])

            serializer = CustomerSerializer(cust,data=request.data)
            if serializer.is_valid():
                # save transaction
                serializer.save()

                Fin_Customers_History.objects.create(
                    Company = com,
                    LoginDetails = data,
                    customer = Fin_Customers.objects.get(id=serializer.data['id']),
                    action = 'Edited'
                )

                return Response(
                    {"status": True, "data": serializer.data}, status=status.HTTP_200_OK
                )
            else:
                return Response(
                    {"status": False, "data": serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST,
                )
    except Exception as e:
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

@api_view(("GET",))
def custCreditLimitAlerts(request, id):
    try:
        s_id = id
        data = Fin_Login_Details.objects.get(id=s_id)
        if data.User_Type != 'Distributor':
            if data.User_Type == "Company":
                com = Fin_Company_Details.objects.get(Login_Id = s_id)
            elif data.User_Type == 'Staff':
                com = Fin_Staff_Details.objects.get(Login_Id = s_id).company_id
            
            customers = Fin_Customers.objects.filter(Company = com)

            if Fin_CNotification.objects.filter(Company_id=com, Customers__isnull=False).exists():
                alertItems = Fin_CNotification.objects.filter(Company_id=com, Customers__isnull=False)
                for c in alertItems:
                    cust = Fin_Customers.objects.get(id = c.Customers.id)
                    if cust.credit_limit > 0 and cust.credit_limit > cust.current_balance:
                        c.status = 'Old'
                        c.save()
                    else:
                        c.status = 'New'
                        c.save()
                
                for itm in customers:
                    if not Fin_CNotification.objects.filter(Customers = itm).exists():
                        if itm.credit_limit > 0 and itm.current_balance > itm.credit_limit:
                            Fin_CNotification.objects.create(Company_id = com, Login_Id = data, Customers = itm, Title = 'Customer Credit Limit Alert.!!', Discription = f'{itm.first_name} {itm.last_name} has been exceeded the credit limit..')

            else:
                for itm in customers:
                    if itm.credit_limit > 0 and itm.current_balance > itm.credit_limit:
                        Fin_CNotification.objects.create(Company_id = com, Login_Id = data, Customers = itm, Title = 'Customer Credit Limit Alert.!!', Discription = f'{itm.first_name} {itm.last_name} has been exceeded the credit limit..')
            
            custCreditLimit = Fin_CNotification.objects.filter(Company_id = com, Customers__isnull=False, status = 'New')
            nCount = Fin_CNotification.objects.filter(Company_id = com, status = 'New')
            if custCreditLimit:
                serializer = CNotificationsSerializer(custCreditLimit, many=True)
                return Response(
                    {"status": True, "custCreditLimit": serializer.data, 'count':len(nCount)},
                    status=status.HTTP_200_OK,
                )
            else:
                return Response(
                    {"status": True, "custCreditLimit": None, 'count':len(nCount)},
                    status=status.HTTP_200_OK,
                )
        else:
            return Response({"status": False},status=status.HTTP_200_OK)
    except Exception as e:
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

# Price Lists
@api_view(("GET",))
def Fin_getNewPriceListItems(request, id):
    try:
        data = Fin_Login_Details.objects.get(id=id)
        if data.User_Type == 'Company':
            cmp = Fin_Company_Details.objects.get(Login_Id=id)
        else:
            cmp = Fin_Staff_Details.objects.get(Login_Id = id).company_id
        
        items = Fin_Items.objects.filter(Company = cmp, status = 'Active').order_by('name')
        serializer = ItemSerializer(items, many=True)
        return Response(
            {"status": True, "items": serializer.data}, status=status.HTTP_200_OK
        )
    except Exception as e:
        print(e)
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

@api_view(("POST",))
def Fin_createNewPriceList(request):
    try:
        s_id = request.data["Id"]
        data = Fin_Login_Details.objects.get(id=s_id)
        if data.User_Type == "Company":
            com = Fin_Company_Details.objects.get(Login_Id=s_id)
        else:
            com = Fin_Staff_Details.objects.get(Login_Id=s_id).company_id

        name = request.data['name']
        if Fin_Price_List.objects.filter(Company = com, name__iexact = name).exists():
            return Response({'status':False,'message':f'{name} already exists, try another'})
        else:
            request.data['LoginDetails'] = data.id
            request.data['Company'] = com.id

            itmRt = request.data['item_rate']

            serializer = PriceListSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                priceList = Fin_Price_List.objects.get(id=serializer.data['id'])

                if itmRt == 'Customized individual rate':
                    items = request.data['list_items']
                    for i in items:

                        itemId = i.get('id')
                        stdRate = i.get('salesRate') if request.data['type'] == 'Sales' else i.get('purchaseRate')
                        customRate = 0 if i.get('customRate') == "" else i.get('customRate')
                        Fin_PriceList_Items.objects.create(Company = com, LoginDetails = data, list = priceList, item = Fin_Items.objects.get(id = itemId), standard_rate = float(stdRate), custom_rate = float(customRate))
                    
                Fin_PriceList_Transaction_History.objects.create(
                    Company = com,
                    LoginDetails = data,
                    list = priceList,
                    action = 'Created'
                )

                return Response({'status':True, 'data':serializer.data}, status=status.HTTP_200_OK)
            else:
                return Response({'status':False, 'data':serializer.errors}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(("GET",))
def Fin_fetchPriceLists(request, id):
    try:
        data = Fin_Login_Details.objects.get(id=id)
        if data.User_Type == "Company":
            com = Fin_Company_Details.objects.get(Login_Id=id)
        else:
            com = Fin_Staff_Details.objects.get(Login_Id=id).company_id

        priceLists = Fin_Price_List.objects.filter(Company=com)
        serializer = PriceListSerializer(priceLists, many=True)
        return Response(
            {"status": True, "priceLists": serializer.data}, status=status.HTTP_200_OK
        )
    except Exception as e:
        print(e)
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

@api_view(("GET",))
def Fin_fetchPLDetails(request, id):
    try:
        pl = Fin_Price_List.objects.get(id=id)
        plItems = Fin_PriceList_Items.objects.filter(list = pl)
        hist = Fin_PriceList_Transaction_History.objects.filter(list=pl).last()
        his = None
        plItms = []
        if hist:
            his = {
                "action": hist.action,
                "date": hist.date,
                "doneBy": hist.LoginDetails.First_name
                + " "
                + hist.LoginDetails.Last_name,
            }
        
        if plItems:
            for i in plItems:
                p = {
                    'id':i.item.id,
                    'name': i.item.name,
                    'salesRate': i.item.selling_price,
                    'purchaseRate': i.item.purchase_price,
                    'stdRate': i.standard_rate,
                    'customRate': i.custom_rate
                }
                plItms.append(p)
                
        cmt = Fin_PriceList_Comments.objects.filter(list=pl)
        plSerializer = PriceListSerializer(pl)
        commentsSerializer = PriceListCommentsSerializer(cmt, many=True)
     
        return Response(
            {
                "status": True,
                "priceList": plSerializer.data,
                "history": his,
                "comments": commentsSerializer.data,
                "items": plItms
            },
            status=status.HTTP_200_OK,
        )
    except Exception as e:
        print(e)
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

@api_view(("POST",))
def Fin_changePLStatus(request):
    try:
        plId = request.data["id"]
        data = Fin_Price_List.objects.get(id=plId)
        data.status = request.data["status"]
        data.save()
        return Response({"status": True}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

@api_view(("POST",))
def Fin_addPLComment(request):
    try:
        id = request.data["Id"]
        data = Fin_Login_Details.objects.get(id=id)
        if data.User_Type == "Company":
            com = Fin_Company_Details.objects.get(Login_Id=id)
        else:
            com = Fin_Staff_Details.objects.get(Login_Id=id).company_id

        request.data["Company"] = com.id
        serializer = PriceListCommentsSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"status": True, "data": serializer.data}, status=status.HTTP_200_OK
            )
        else:
            return Response(
                {"status": False, "data": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
    except Exception as e:
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

@api_view(("DELETE",))
def Fin_deletePLComment(request, id):
    try:
        cmt = Fin_PriceList_Comments.objects.get(id=id)
        cmt.delete()
        return Response({"status": True}, status=status.HTTP_200_OK)
    except Exception as e:
        print(e)
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

@api_view(("DELETE",))
def Fin_deletePriceList(request, id):
    try:
        pl = Fin_Price_List.objects.get(id=id)
        pl.delete()
        return Response({"status": True}, status=status.HTTP_200_OK)
    except Exception as e:
        print(e)
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

@api_view(("GET",))
def Fin_fetchPLHistory(request, id):
    try:
        pl = Fin_Price_List.objects.get(id=id)
        hist = Fin_PriceList_Transaction_History.objects.filter(list=pl)
        his = []
        if hist:
            for i in hist:
                h = {
                    "action": i.action,
                    "date": i.date,
                    "name": i.LoginDetails.First_name + " " + i.LoginDetails.Last_name,
                }
                his.append(h)
        plSerializer = PriceListSerializer(pl)
        return Response(
            {"status": True, "priceList": plSerializer.data, "history": his},
            status=status.HTTP_200_OK,
        )
    except Exception as e:
        print(e)
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

@api_view(("GET",))
def Fin_priceListPdf(request):
    try:
        id = request.GET['Id']
        plId = request.GET['pl_id']

        data = Fin_Login_Details.objects.get(id=id)
        if data.User_Type == "Company":
            com = Fin_Company_Details.objects.get(Login_Id=id)
        else:
            com = Fin_Staff_Details.objects.get(Login_Id=id).company_id

        lst = Fin_Price_List.objects.get(id=plId)
        plItems = Fin_PriceList_Items.objects.filter(list = lst)
        context = {'list': lst, 'plItems':plItems}
        
        template_path = 'company/Fin_PriceListView_Pdf.html'
        fname = 'Price_List_'+lst.name
        # Create a Django response object, and specify content_type as pdftemp_
        response = HttpResponse(content_type="application/pdf")
        response["Content-Disposition"] = f"attachment; filename = {fname}.pdf"
        # find the template and render it.
        template = get_template(template_path)
        html = template.render(context)

        # create a pdf
        pisa_status = pisa.CreatePDF(html, dest=response)
        # if error then show some funny view
        if pisa_status.err:
            return HttpResponse("We had some errors <pre>" + html + "</pre>")
        return response
    except Exception as e:
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

@api_view(("POST",))
def Fin_sharePLDetailsToEmail(request):
    try:
        id = request.data["Id"]
        data = Fin_Login_Details.objects.get(id=id)
        if data.User_Type == "Company":
            com = Fin_Company_Details.objects.get(Login_Id=id)
        else:
            com = Fin_Staff_Details.objects.get(Login_Id=id).company_id

        plId = request.data["pl_id"]
        lst = Fin_Price_List.objects.get(id=plId)
        plItems = Fin_PriceList_Items.objects.filter(list = lst)
        emails_string = request.data["email_ids"]

        # Split the string by commas and remove any leading or trailing whitespace
        emails_list = [email.strip() for email in emails_string.split(",")]
        email_message = request.data["email_message"]
        # print(emails_list)

        context = {'list': lst, 'plItems':plItems}
        template_path = 'company/Fin_PriceListView_Pdf.html'
        template = get_template(template_path)

        html = template.render(context)
        result = BytesIO()
        pdf = pisa.pisaDocument(BytesIO(html.encode("ISO-8859-1")), result)
        pdf = result.getvalue()
        filename = f'Price_list_{lst.name}.pdf'
        subject = f"Price_list_{lst.name}"
        email = EmailMessage(
            subject,
            f"Hi,\nPlease find the attached details - Price List-{lst.name}. \n{email_message}\n\n--\nRegards,\n{com.Company_name}\n{com.Address}\n{com.State} - {com.Country}\n{com.Contact}",
            from_email=settings.EMAIL_HOST_USER,
            to=emails_list,
        )
        email.attach(filename, pdf, "application/pdf")
        email.send(fail_silently=False)

        return Response({"status": True}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

@api_view(("PUT",))
def Fin_updatePriceList(request):
    try:
        s_id = request.data["Id"]
        data = Fin_Login_Details.objects.get(id=s_id)
        if data.User_Type == "Company":
            com = Fin_Company_Details.objects.get(Login_Id=s_id)
        else:
            com = Fin_Staff_Details.objects.get(Login_Id=s_id).company_id

        list = Fin_Price_List.objects.get(id=request.data['pl_id'])
        name = request.data['name']
        if name != list.name and Fin_Price_List.objects.filter(Company = com, name__iexact = name).exists():
            return Response({'status':False,'message':f'{name} already exists, try another'})
        else:
            itmRt = request.data['item_rate']

            serializer = PriceListSerializer(list,data=request.data)
            if serializer.is_valid():
                serializer.save()
                priceList = Fin_Price_List.objects.get(id=serializer.data['id'])

                Fin_PriceList_Items.objects.filter(list=list).delete()
                if itmRt == 'Customized individual rate':
                    items = request.data['list_items']
                    for i in items:

                        itemId = i.get('id')
                        stdRate = i.get('salesRate') if request.data['type'] == 'Sales' else i.get('purchaseRate')
                        customRate = 0 if i.get('customRate') == "" else i.get('customRate')
                        Fin_PriceList_Items.objects.create(Company = com, LoginDetails = data, list = priceList, item = Fin_Items.objects.get(id = itemId), standard_rate = float(stdRate), custom_rate = float(customRate))
                    
                Fin_PriceList_Transaction_History.objects.create(
                    Company = com,
                    LoginDetails = data,
                    list = priceList,
                    action = 'Edited'
                )

                return Response({'status':True, 'data':serializer.data}, status=status.HTTP_200_OK)
            else:
                return Response({'status':False, 'data':serializer.errors}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
        
        
# Banking

@api_view(("GET",))
def Fin_fetchBanks(request, id):
    try:
        data = Fin_Login_Details.objects.get(id=id)
        if data.User_Type == "Company":
            com = Fin_Company_Details.objects.get(Login_Id=id)
        else:
            com = Fin_Staff_Details.objects.get(Login_Id=id).company_id

        banks = Fin_Banking.objects.filter(company = com)
        serializer = BankSerializer(banks, many=True)
        return Response(
            {"status": True, "banks": serializer.data}, status=status.HTTP_200_OK
        )
    except Exception as e:
        print(e)
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

@api_view(("GET",))
def Fin_checkBankAccountNumber(request):
    try:
        data = Fin_Login_Details.objects.get(id=request.GET['Id'])
        if data.User_Type == 'Company':
            cmp = Fin_Company_Details.objects.get(Login_Id=data)
        else:
            cmp = Fin_Staff_Details.objects.get(Login_Id = data).company_id
        
        bank = request.GET['bank']
        num = request.GET['number']
        if Fin_Banking.objects.filter(company = cmp, bank_name__iexact = bank, account_number__iexact = num).exists():
            return Response({'is_exist':True, 'message':f'{num} already exists, Try another.!'})
        else:
            return Response({'is_exist':False})
    except Exception as e:
        print(e)
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

@api_view(("POST",))
def Fin_createNewBank(request):
    try:
        s_id = request.data["Id"]
        data = Fin_Login_Details.objects.get(id=s_id)
        if data.User_Type == "Company":
            com = Fin_Company_Details.objects.get(Login_Id=s_id)
        else:
            com = Fin_Staff_Details.objects.get(Login_Id=s_id).company_id

        request.data["company"] = com.id
        request.data["login_details"] = com.Login_Id.id
        request.data["opening_balance"] = -1 * float(request.data['opening_balance']) if request.data['opening_balance_type'] == 'CREDIT' else float(request.data['opening_balance'])
        date_str = request.data['date']

        # Appending the default time '00:00:00' to the date string
        datetime_str = f"{date_str} 00:00:00"

        # Converting the combined string to a datetime object
        dt = datetime.strptime(datetime_str, '%Y-%m-%d %H:%M:%S')
        request.data['date'] = dt

        if Fin_Banking.objects.filter(company = com, bank_name__iexact = request.data['bank_name'], account_number__iexact = request.data['account_number']).exists():
            return Response({"status": False, "message": "Account Number already exists"})
        else:
            serializer = BankSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                bank = Fin_Banking.objects.get(id=serializer.data['id'])
                
                # save transactions
                banking_history = Fin_BankingHistory(
                    login_details = data,
                    company = com,
                    banking = bank,
                    action = 'Created'
                )
                banking_history.save()
                
                transaction=Fin_BankTransactions(
                    login_details = data,
                    company = com,
                    banking = bank,
                    amount = request.data['opening_balance'],
                    adjustment_date = request.data['date'],
                    transaction_type = "Opening Balance",
                    from_type = '',
                    to_type = '',
                    current_balance = request.data['opening_balance']
                    
                )
                transaction.save()

                transaction_history = Fin_BankTransactionHistory(
                    login_details = data,
                    company = com,
                    bank_transaction = transaction,
                    action = 'Created'
                )
                transaction_history.save()
                return Response(
                    {"status": True, "data": serializer.data}, status=status.HTTP_200_OK
                )
            else:
                return Response(
                    {"status": False, "data": serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST,
                )
    except Exception as e:
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

@api_view(("GET",))
def Fin_fetchBankDetails(request, id):
    try:
        bank = Fin_Banking.objects.get(id=id)
        hist = Fin_BankingHistory.objects.filter(banking=bank).last()
        his = None
        if hist:
            his = {
                "action": hist.action,
                "date": hist.date,
                "doneBy": hist.login_details.First_name
                + " "
                + hist.login_details.Last_name,
            }

        cmt = Fin_BankingComments.objects.filter(banking=bank)
        trans = Fin_BankTransactions.objects.filter(banking=bank) 

        bnkSerializer = BankSerializer(bank)
        commentsSerializer = BankCommentsSerializer(cmt, many=True)
        transSerializer = BankTransactionsSerializer(trans, many=True)
        updt = bank.login_details.First_name+" "+bank.login_details.Last_name if bank.login_details else ""
        return Response(
            {
                "status": True,
                "bank": bnkSerializer.data,
                "history": his,
                "comments": commentsSerializer.data,
                "transactions": transSerializer.data,
                "lastUpdated": updt,
            },
            status=status.HTTP_200_OK,
        )
    except Exception as e:
        print(e)
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

@api_view(("GET",))
def Fin_fetchBankTransactionHistory(request, id):
    try:
        trns = Fin_BankTransactions.objects.get(id=id)
        hist = Fin_BankTransactionHistory.objects.filter(bank_transaction=trns)
        his = []
        if hist:
            for i in hist:
                h = {
                    "action": i.action,
                    "date": i.date,
                    "name": i.login_details.First_name + " " + i.login_details.Last_name,
                }
                his.append(h)
        bnkSerializer = BankSerializer(trns.banking)
        return Response(
            {"status": True, "bank": bnkSerializer.data, "history": his},
            status=status.HTTP_200_OK,
        )
    except Exception as e:
        print(e)
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

@api_view(("DELETE",))
def Fin_deleteBankTransaction(request, id):
    try:
        transaction = Fin_BankTransactions.objects.get(id=id)
        bank = Fin_Banking.objects.get(id=transaction.banking_id)
        #   transfer_to = Fin_BankTransactions.objects.get(id=transaction.bank_to_bank)
        try:
                transfer_to = Fin_BankTransactions.objects.get(id=transaction.bank_to_bank)
        except:
                transfer_to = None

        try:
                bank_to = Fin_Banking.objects.get(id=transfer_to.banking.id)
        except:
                transfer_to = None


        if transaction.transaction_type=='Cash Withdraw':
            bank.current_balance = bank.current_balance + transaction.amount
        elif transaction.transaction_type=='Cash Deposit':
            bank.current_balance = bank.current_balance - transaction.amount
        elif transaction.adjustment_type=='Reduce Balance':
            bank.current_balance = bank.current_balance + transaction.amount
        elif transaction.adjustment_type=='Increase Balance':
            bank.current_balance = bank.current_balance - transaction.amount
        elif transaction.transaction_type=='From Bank Transfer':
            bank.current_balance = bank.current_balance + transaction.amount
            bank_to.current_balance = bank_to.current_balance - transfer_to.amount
        elif transaction.transaction_type=='To Bank Transfer':
            bank.current_balance = bank.current_balance - transaction.amount
            bank_to.current_balance = bank_to.current_balance + transfer_to.amount
        else:
            bank.current_balance = bank.current_balance - transaction.amount
        
        bank.save()
        try:
            bank_to.save()
        except:
            bank_to = None
        transaction.delete()
        try:
            transfer_to.delete()
        except:
            transfer_to = None

        return Response({"status": True}, status=status.HTTP_200_OK)
    except Exception as e:
        print(e)
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

@api_view(("PUT",))
def Fin_updateBank(request):
    try:
        s_id = request.data["Id"]
        data = Fin_Login_Details.objects.get(id=s_id)
        if data.User_Type == "Company":
            com = Fin_Company_Details.objects.get(Login_Id=s_id)
        else:
            com = Fin_Staff_Details.objects.get(Login_Id=s_id).company_id

        bank = Fin_Banking.objects.get(id=request.data['b_id'])
        old_op_blnc = float(bank.opening_balance)
        try:
            trans = Fin_BankTransactions.objects.get(banking = bank, transaction_type = "Opening Balance")
        except:
            trans = None

        request.data["company"] = com.id
        request.data["login_details"] = com.Login_Id.id
        request.data["opening_balance"] = -1 * float(request.data['opening_balance']) if request.data['opening_balance_type'] == 'CREDIT' else float(request.data['opening_balance'])
        opening_balance = request.data["opening_balance"]

        date_str = request.data['date']

        # Appending the default time '00:00:00' to the date string
        datetime_str = f"{date_str} 00:00:00"

        # Converting the combined string to a datetime object
        dt = datetime.strptime(datetime_str, '%Y-%m-%d %H:%M:%S')
        request.data['date'] = dt

        if bank.account_number != request.data['account_number'] and bank.bank_name != request.data['bank_name'] and Fin_Banking.objects.filter(company = com, bank_name__iexact = request.data['bank_name'], account_number__iexact = request.data['account_number']).exists():
            return Response({"status": False, "message": "Account Number already exists"})
        else:
            if old_op_blnc == float(opening_balance):
                request.data['current_balance'] = bank.current_balance
                serializer = BankSerializer(bank,data=request.data)
                if serializer.is_valid():
                    serializer.save()
                    banking_history = Fin_BankingHistory(
                        login_details = data,
                        company = com,
                        banking = bank,
                        action = 'Updated'
                    )
                    banking_history.save()
                    return Response(
                        {"status": True, "data": serializer.data}, status=status.HTTP_200_OK
                    )
                else:
                    return Response(
                        {"status": False, "data": serializer.errors},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
            elif old_op_blnc < int(opening_balance): 
                increased_amount =  float(opening_balance) - old_op_blnc 
                request.data['current_balance'] = bank.current_balance + increased_amount
                serializer = BankSerializer(bank,data=request.data)
                if serializer.is_valid():
                    serializer.save()
                    banking_history = Fin_BankingHistory(
                        login_details = data,
                        company = com,
                        banking = bank,
                        action = 'Updated'
                    )
                    banking_history.save()

                    if trans:
                        trans.amount += float(increased_amount)
                        trans.current_balance +=float(increased_amount)
                        trans.save()

                        transaction_history = Fin_BankTransactionHistory(
                            login_details = data,
                            company = com,
                            bank_transaction = trans,
                            action = 'Updated'
                        )
                        transaction_history.save()
                    return Response(
                        {"status": True, "data": serializer.data}, status=status.HTTP_200_OK
                    )
                else:
                    return Response(
                        {"status": False, "data": serializer.errors},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
            elif old_op_blnc > int(opening_balance): 
                decreased_amount =  old_op_blnc - float(opening_balance)
                request.data['current_balance'] = bank.current_balance - decreased_amount
                serializer = BankSerializer(bank,data=request.data)
                if serializer.is_valid():
                    serializer.save()
                    banking_history = Fin_BankingHistory(
                        login_details = data,
                        company = com,
                        banking = bank,
                        action = 'Updated'
                    )
                    banking_history.save()

                    if trans:
                        trans.amount -= float(decreased_amount)
                        trans.current_balance -=float(decreased_amount)
                        trans.save()

                        transaction_history = Fin_BankTransactionHistory(
                            login_details = data,
                            company = com,
                            bank_transaction = trans,
                            action = 'Updated'
                        )
                        transaction_history.save()
                    return Response(
                        {"status": True, "data": serializer.data}, status=status.HTTP_200_OK
                    )
                else:
                    return Response(
                        {"status": False, "data": serializer.errors},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
    except Exception as e:
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

@api_view(("POST",))
def Fin_changeBankStatus(request):
    try:
        bnkId = request.data["id"]
        data = Fin_Banking.objects.get(id=bnkId)
        data.bank_status = request.data["status"]
        data.save()
        return Response({"status": True}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

@api_view(("POST",))
@parser_classes((MultiPartParser, FormParser))
def Fin_addBankingAttachment(request):
    try:
        s_id = request.data["Id"]
        data = Fin_Login_Details.objects.get(id=s_id)
        if data.User_Type == "Company":
            com = Fin_Company_Details.objects.get(Login_Id=s_id)
        else:
            com = Fin_Staff_Details.objects.get(Login_Id=s_id).company_id

        request.data["company"] = com.id
        request.data["login_details"] = com.Login_Id.id
        serializer = BankAttachmentSerializer(data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"status": True, "data": serializer.data}, status=status.HTTP_200_OK
            )
        else:
            return Response(
                {"status": False, "data": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
    except Exception as e:
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

@api_view(("DELETE",))
def Fin_deleteBank(request, id):
    try:
        bank = Fin_Banking.objects.get(id=id)
        trans = Fin_BankTransactions.objects.filter(banking=bank).exclude(transaction_type = 'Opening Balance')
        if trans:
            bank.bank_status = 'Inactive'
            bank.save()
            return Response({"status": False, 'message': 'Bank already have some transactions so the status has been changed to Inactive'}, status=status.HTTP_200_OK)
        else:
            bank.delete()
            return Response({"status": True}, status=status.HTTP_200_OK)
    except Exception as e:
        print(e)
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

@api_view(("POST",))
def Fin_saveBankToCash(request):
    try:
        s_id = request.data["Id"]
        data = Fin_Login_Details.objects.get(id=s_id)
        if data.User_Type == "Company":
            com = Fin_Company_Details.objects.get(Login_Id=s_id)
        else:
            com = Fin_Staff_Details.objects.get(Login_Id=s_id).company_id

        f_bank = request.data['bank']
        amount = int(request.data['amount'])
        adj_date = request.data['date']
        desc = request.data['description']

        

        bank = Fin_Banking.objects.get(id=f_bank)
        bank.current_balance -= amount
        bank.save()
        
        transaction = Fin_BankTransactions(
            login_details = data,
            company = com,
            banking = bank,
            from_type = '',
            to_type='',
            amount=amount,
            description=desc,
            adjustment_date=adj_date,
            transaction_type='Cash Withdraw',
            current_balance= bank.current_balance               
        )
        transaction.save()
        transaction_history = Fin_BankTransactionHistory(
            login_details = data,
            company = com,
            bank_transaction = transaction,
            action = 'Created'
        )
        transaction_history.save()

        return Response({"status": True}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

@api_view(("POST",))
def Fin_saveCashToBank(request):
    try:
        s_id = request.data["Id"]
        data = Fin_Login_Details.objects.get(id=s_id)
        if data.User_Type == "Company":
            com = Fin_Company_Details.objects.get(Login_Id=s_id)
        else:
            com = Fin_Staff_Details.objects.get(Login_Id=s_id).company_id

        t_bank = request.data['bank']
        amount = int(request.data['amount'])
        adj_date = request.data['date']
        desc = request.data['description']

        

        bank = Fin_Banking.objects.get(id=t_bank)
        bank.current_balance += amount
        bank.save()
        
        transaction = Fin_BankTransactions(
            login_details = data,
            company = com,
            banking = bank,
            from_type = '',
            to_type='',
            amount=amount,
            description=desc,
            adjustment_date=adj_date,
            transaction_type='Cash Deposit',
            current_balance= bank.current_balance               
        )
        transaction.save()
        transaction_history = Fin_BankTransactionHistory(
            login_details = data,
            company = com,
            bank_transaction = transaction,
            action = 'Created'
        )
        transaction_history.save()

        return Response({"status": True}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

@api_view(("POST",))
def Fin_saveBankToBank(request):
    try:
        s_id = request.data["Id"]
        data = Fin_Login_Details.objects.get(id=s_id)
        if data.User_Type == "Company":
            com = Fin_Company_Details.objects.get(Login_Id=s_id)
        else:
            com = Fin_Staff_Details.objects.get(Login_Id=s_id).company_id

        f_bank = request.data['f_bank']
        t_bank = request.data['t_bank']
        amount = int(request.data['amount'])
        adj_date = request.data['date']
        desc = request.data['description']

        from_bank = Fin_Banking.objects.get(id=f_bank)
        to_bank = Fin_Banking.objects.get(id=t_bank)
        to_bank.current_balance += amount
        from_bank.current_balance -= amount
        to_bank.save()
        from_bank.save()

        transaction_withdraw = Fin_BankTransactions(
            login_details = data,
            company = com,
            banking = from_bank,
            from_type = 'From :' + from_bank.bank_name,
            to_type='To :' + to_bank.bank_name,
            amount=amount,
            description=desc,
            adjustment_date=adj_date,
            transaction_type='From Bank Transfer', 
            current_balance= from_bank.current_balance,
                            
        )
        transaction_withdraw.save()
        transaction_history = Fin_BankTransactionHistory(
            login_details = data,
            company = com,
            bank_transaction = transaction_withdraw,
            action = 'Created'
        )
        transaction_history.save()

        transaction_deposit = Fin_BankTransactions(
            login_details = data,
            company = com,
            banking = to_bank,
            from_type = 'From :' + from_bank.bank_name,
            to_type='To :' + to_bank.bank_name,
            amount=amount,
            description=desc,
            adjustment_date=adj_date,
            transaction_type='To Bank Transfer', 
            current_balance= to_bank.current_balance,
        )
        transaction_deposit.save()
        transaction_history = Fin_BankTransactionHistory(
            login_details = data,
            company = com,
            bank_transaction = transaction_deposit,
            action = 'Created'
        )
        transaction_history.save()

        transaction_withdraw.bank_to_bank = transaction_deposit.id
        transaction_deposit.bank_to_bank = transaction_withdraw.id
        transaction_withdraw.save()
        transaction_deposit.save()

        return Response({"status": True}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

@api_view(("POST",))
def Fin_saveBankAdjust(request):
    try:
        s_id = request.data["Id"]
        data = Fin_Login_Details.objects.get(id=s_id)
        if data.User_Type == "Company":
            com = Fin_Company_Details.objects.get(Login_Id=s_id)
        else:
            com = Fin_Staff_Details.objects.get(Login_Id=s_id).company_id

        t_bank = request.data['bank']
        amount = int(request.data['amount'])
        adj_date = request.data['date']
        adj_type = request.data['type']
        desc = request.data['description']

        bank = Fin_Banking.objects.get(id=t_bank)

        if adj_type == 'Increase Balance':
            bank.current_balance += amount
            bank.save()
        else:
            bank.current_balance -= amount
            bank.save()
            
        transaction = Fin_BankTransactions(
            login_details = data,
            company = com,
            banking = bank,
            from_type = '',
            to_type='',
            amount=amount,
            description=desc,
            adjustment_date=adj_date,
            transaction_type='Adjust bank Balance', 
            current_balance= bank.current_balance,     
        )
        transaction.save()

        if adj_type == 'Increase Balance':
            transaction.adjustment_type = 'Increase Balance'
            transaction.save()
        else:
            transaction.adjustment_type = 'Reduce Balance'
            transaction.save()
        
        transaction_history = Fin_BankTransactionHistory(
            login_details = data,
            company = com,
            bank_transaction = transaction,
            action = 'Created'
        )
        transaction_history.save()

        return Response({"status": True}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

@api_view(("GET",))
def Fin_bankStatementPdf(request):
    try:
        id = request.GET['Id']
        bnkId = request.GET['b_id']

        data = Fin_Login_Details.objects.get(id=id)
        if data.User_Type == "Company":
            com = Fin_Company_Details.objects.get(Login_Id=id)
        else:
            com = Fin_Staff_Details.objects.get(Login_Id=id).company_id

        bnk = Fin_Banking.objects.get(id=bnkId)
        trns = Fin_BankTransactions.objects.filter(banking=bnk)
        context = {'bank': bnk, 'trans':trns}
        
        template_path = 'company/Fin_Bank_Statement_Pdf.html'
        fname = 'Bank_Statement_'+bnk.bank_name
        # Create a Django response object, and specify content_type as pdftemp_
        response = HttpResponse(content_type="application/pdf")
        response["Content-Disposition"] = f"attachment; filename = {fname}.pdf"
        # find the template and render it.
        template = get_template(template_path)
        html = template.render(context)

        # create a pdf
        pisa_status = pisa.CreatePDF(html, dest=response)
        # if error then show some funny view
        if pisa_status.err:
            return HttpResponse("We had some errors <pre>" + html + "</pre>")
        return response
    except Exception as e:
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

@api_view(("POST",))
def Fin_shareBankStatementToEmail(request):
    try:
        id = request.data["Id"]
        data = Fin_Login_Details.objects.get(id=id)
        if data.User_Type == "Company":
            com = Fin_Company_Details.objects.get(Login_Id=id)
        else:
            com = Fin_Staff_Details.objects.get(Login_Id=id).company_id

        bnkId = request.data["b_id"]

        emails_string = request.data["email_ids"]

        # Split the string by commas and remove any leading or trailing whitespace
        emails_list = [email.strip() for email in emails_string.split(",")]
        email_message = request.data["email_message"]
        # print(emails_list)

        bnk = Fin_Banking.objects.get(id=bnkId)
        trns = Fin_BankTransactions.objects.filter(banking=bnk)
        context = {'bank': bnk, 'trans':trns}
        
        template_path = 'company/Fin_Bank_Statement_Pdf.html'
        template = get_template(template_path)

        html = template.render(context)
        result = BytesIO()
        pdf = pisa.pisaDocument(BytesIO(html.encode("ISO-8859-1")), result)
        pdf = result.getvalue()
        filename = f'Bank_Statement_{bnk.bank_name}.pdf'
        subject = f"Bank_Statement_{bnk.bank_name}"
        email = EmailMessage(
            subject,
            f"Hi,\nPlease find the attached Transaction details - STATEMENT-{bnk.bank_name}. \n{email_message}\n\n--\nRegards,\n{com.Company_name}\n{com.Address}\n{com.State} - {com.Country}\n{com.Contact}",
            from_email=settings.EMAIL_HOST_USER,
            to=emails_list,
        )
        email.attach(filename, pdf, "application/pdf")
        email.send(fail_silently=False)

        return Response({"status": True}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

@api_view(("GET",))
def Fin_getTransactionDetails(request, id):
    try:
        trans = Fin_BankTransactions.objects.get(id=id)
        bank = trans.banking
        try:
            otherBank = Fin_BankTransactions.objects.get(id=trans.bank_to_bank).banking.id
        except:
            otherBank = None

        bnkSerializer = BankSerializer(bank)
        transSerializer = BankTransactionsSerializer(trans)
        return Response(
            {
                "status": True,
                "bank": bnkSerializer.data,
                "transaction": transSerializer.data,
                "otherBank": otherBank
            },
            status=status.HTTP_200_OK,
        )
    except Exception as e:
        print(e)
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

@api_view(("POST",))
def Fin_updateBankToCash(request):
    try:
        s_id = request.data["Id"]
        data = Fin_Login_Details.objects.get(id=s_id)
        if data.User_Type == "Company":
            com = Fin_Company_Details.objects.get(Login_Id=s_id)
        else:
            com = Fin_Staff_Details.objects.get(Login_Id=s_id).company_id

        f_bank = request.data['bank']
        amount = int(request.data['amount'])
        adj_date = request.data['date']
        desc = request.data['description']

        transaction = Fin_BankTransactions.objects.get(id=request.data['t_id'])

        bank = Fin_Banking.objects.get(id=f_bank)
        bank.current_balance = bank.current_balance -(int(amount) - transaction.amount)
        bank.save()
        
        transaction.amount=amount
        transaction.description=desc
        transaction.adjustment_date=adj_date
        transaction.current_balance= bank.current_balance               
        
        transaction.save()
        transaction_history = Fin_BankTransactionHistory(
            login_details = data,
            company = com,
            bank_transaction = transaction,
            action = 'Updated'
        )
        transaction_history.save()

        return Response({"status": True}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

@api_view(("POST",))
def Fin_updateCashToBank(request):
    try:
        s_id = request.data["Id"]
        data = Fin_Login_Details.objects.get(id=s_id)
        if data.User_Type == "Company":
            com = Fin_Company_Details.objects.get(Login_Id=s_id)
        else:
            com = Fin_Staff_Details.objects.get(Login_Id=s_id).company_id

        f_bank = request.data['bank']
        amount = int(request.data['amount'])
        adj_date = request.data['date']
        desc = request.data['description']

        transaction = Fin_BankTransactions.objects.get(id=request.data['t_id'])

        bank = Fin_Banking.objects.get(id=f_bank)
        bank.current_balance = bank.current_balance + (int(amount) - transaction.amount)
        bank.save()
        
        transaction.amount=amount
        transaction.description=desc
        transaction.adjustment_date=adj_date
        transaction.current_balance= bank.current_balance               
        
        transaction.save()
        transaction_history = Fin_BankTransactionHistory(
            login_details = data,
            company = com,
            bank_transaction = transaction,
            action = 'Updated'
        )
        transaction_history.save()

        return Response({"status": True}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

@api_view(("POST",))
def Fin_updateBankAdjust(request):
    try:
        s_id = request.data["Id"]
        data = Fin_Login_Details.objects.get(id=s_id)
        if data.User_Type == "Company":
            com = Fin_Company_Details.objects.get(Login_Id=s_id)
        else:
            com = Fin_Staff_Details.objects.get(Login_Id=s_id).company_id

        transaction = Fin_BankTransactions.objects.get(id=request.data['t_id'])

        f_bank = request.data['bank']
        type = request.data['type']
        amount = int(request.data['amount'])
        adj_date = request.data['date']
        desc = request.data['description']


        bank = Fin_Banking.objects.get(id=f_bank)
        if type == 'Increase Balance':
            bank.current_balance = bank.current_balance + (int(amount) - transaction.amount)
            bank.save()
        else:
            bank.current_balance = bank.current_balance - (int(amount) - transaction.amount)
            bank.save()
        
        transaction.amount=amount
        transaction.adjustment_type=type
        transaction.description=desc
        transaction.adjustment_date=adj_date
        transaction.current_balance= bank.current_balance
        
        transaction.save()

        transaction_history = Fin_BankTransactionHistory(
            login_details = data,
            company = com,
            bank_transaction = transaction,
            action = 'Updated'
        )
        transaction_history.save()

        return Response({"status": True}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

@api_view(("POST",))
def Fin_updateBankToBank(request):
    try:
        s_id = request.data["Id"]
        data = Fin_Login_Details.objects.get(id=s_id)
        if data.User_Type == "Company":
            com = Fin_Company_Details.objects.get(Login_Id=s_id)
        else:
            com = Fin_Staff_Details.objects.get(Login_Id=s_id).company_id

        fbank_id = request.data['f_bank']
        tbank_id = request.data['t_bank']

        transfer = Fin_BankTransactions.objects.get(id=request.data['t_id'])
        transfer_to = Fin_BankTransactions.objects.get(id=transfer.bank_to_bank)
        old_amt = transfer_to.amount
        old_bank = Fin_Banking.objects.get(id = transfer.banking.id) if transfer.transaction_type == 'To Bank Transfer' else Fin_Banking.objects.get(id = transfer_to.banking.id)
        fbank = Fin_Banking.objects.get(id=fbank_id)
        tbank = Fin_Banking.objects.get(id=tbank_id)

        if tbank_id != old_bank:
            old_bank.current_balance -= old_amt
            old_bank.save()

        amount = request.data['amount']
        adj_date = request.data['date']
        desc = request.data['description']

        # Update the balances of the banking accounts
        current_balance = transfer.current_balance
        current_balance_trans_to = transfer_to.current_balance
        current_balance_fm = fbank.current_balance
        current_balance_to = tbank.current_balance


        if transfer.transaction_type == 'To Bank Transfer':
            if int(amount) > int(transfer.amount):
                fbank.current_balance -= (int(amount) - int(transfer.amount))
                tbank.current_balance += (int(amount) - int(transfer.amount))
                transfer.current_balance += (int(amount) - int(transfer.amount))
                transfer_to.current_balance -= (int(amount) - int(transfer.amount))

            elif int(amount) < int(transfer.amount):
                fbank.current_balance += (int(transfer.amount) - int(amount))
                tbank.current_balance -= (int(transfer.amount)  - int(amount))
                transfer.current_balance -= (int(transfer.amount)  - int(amount))
                transfer_to.current_balance += (int(transfer.amount)  - int(amount))

            else:
                fbank.current_balance = current_balance_fm
                tbank.current_balance = current_balance_to
                transfer.current_balance = current_balance
                transfer_to.current_balance = current_balance_trans_to
            
            fbank.save()
            tbank.save()
            transfer.save()
            transfer_to.save()

        elif transfer.transaction_type == 'From Bank Transfer':
            if int(amount) > int(transfer.amount):
                fbank.current_balance -= (int(amount) - int(transfer.amount))
                tbank.current_balance += (int(amount) - int(transfer.amount))
                transfer.current_balance -= (int(amount) - int(transfer.amount))
                transfer_to.current_balance += (int(amount) - int(transfer.amount))

            elif int(amount) < int(transfer.amount):
                fbank.current_balance += (int(transfer.amount) - int(amount))
                tbank.current_balance -= (int(transfer.amount) - int(amount))
                transfer.current_balance += (int(transfer.amount) - int(amount))
                transfer_to.current_balance -= (int(transfer.amount) - int(amount))

            else:
                fbank.current_balance = current_balance_fm
                tbank.current_balance = current_balance_to
                transfer.current_balance = current_balance
                transfer_to.current_balance = current_balance_trans_to

            fbank.save()
            tbank.save()
            transfer.save()
            transfer_to.save()

        if transfer.transaction_type == 'To Bank Transfer':
            transfer.from_type = 'From : ' + fbank.bank_name
            transfer.to_type = ' To : ' + tbank.bank_name
            transfer.banking=tbank
            transfer_to.from_type = 'From : ' + fbank.bank_name
            transfer_to.to_type = ' To : ' + tbank.bank_name
            transfer_to.banking=fbank
            # if tbank_id != transfer_to.banking:  # Check if the destination bank has changed
            # # Adjust balances for the old and new banks
            #     transfer.banking.current_balance += int(amount)
            #     transfer.save()
            #     tbank.save()
            #     tbank.current_balance == transfer_to.current_balance
        elif transfer.transaction_type == 'From Bank Transfer':
            transfer.from_type = 'From : ' + fbank.bank_name
            transfer.to_type = ' To : ' + tbank.bank_name
            transfer.banking=fbank
            transfer_to.from_type = 'From : ' + fbank.bank_name
            transfer_to.to_type = ' To : ' + tbank.bank_name
            transfer_to.banking=tbank
            # Before saving the changes to transfer and transfer_to
            # if tbank_id != transfer_to.banking:  # Check if the destination bank has changed
            # # Adjust balances for the old and new banks
            #     transfer_to.banking.current_balance += int(amount)
            #     transfer_to.save()
            #     tbank.save()
            #     tbank.current_balance == transfer_to.current_balance


        transfer.amount = amount
        transfer.adjustment_date = adj_date
        transfer.description = desc
        transfer_to.amount = amount
        transfer_to.adjustment_date = adj_date
        transfer_to.description = desc
        
        fbank.save()
        tbank.save()
        transfer.save()
        transfer_to.save()

        

        transaction_history = Fin_BankTransactionHistory(
                login_details = data,
                company = com,
                bank_transaction = transfer,
                action = 'Updated'
            )
        transaction_history.save()

        return Response({"status": True}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
        
        
# Chart of Accounts
@api_view(("GET",))
def Fin_fetchChartOfAccounts(request, id):
    try:
        data = Fin_Login_Details.objects.get(id=id)
        if data.User_Type == "Company":
            com = Fin_Company_Details.objects.get(Login_Id=id)
        else:
            com = Fin_Staff_Details.objects.get(Login_Id=id).company_id

        acc = Fin_Chart_Of_Account.objects.filter(Company = com)
        serializer = AccountsSerializer(acc, many=True)
        return Response(
            {"status": True, "accounts": serializer.data}, status=status.HTTP_200_OK
        )
    except Exception as e:
        print(e)
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
    
@api_view(("POST",))
def Fin_createNewAccount(request):
    try:
        s_id = request.data["Id"]
        data = Fin_Login_Details.objects.get(id=s_id)
        if data.User_Type == "Company":
            com = Fin_Company_Details.objects.get(Login_Id=s_id)
        else:
            com = Fin_Staff_Details.objects.get(Login_Id=s_id).company_id

        createdDate = date.today()
        request.data["Company"] = com.id
        request.data["LoginDetails"] = com.Login_Id.id
        request.data["parent_account"] = (
            request.data["parent_account"]
            if request.data["sub_account"] == True
            else None
        )
        request.data["bank_account_no"] = None if request.data["bank_account_no"] == "" else request.data["bank_account_no"]
        request.data["date"] = createdDate

        # save account and transaction if account doesn't exists already
        if Fin_Chart_Of_Account.objects.filter(
            Company=com, account_name__iexact=request.data["account_name"]
        ).exists():
            return Response(
                {"status": False, "message": "Account Name already exists."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        else:
            serializer = AccountsSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                # save transaction

                Fin_ChartOfAccount_History.objects.create(
                    Company=com,
                    LoginDetails=data,
                    account=Fin_Chart_Of_Account.objects.get(id=serializer.data["id"]),
                    action="Created",
                )
                return Response(
                    {"status": True, "data": serializer.data}, status=status.HTTP_200_OK
                )
            else:
                return Response(
                    {"status": False, "data": serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST,
                )
    except Exception as e:
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

@api_view(("GET",))
def Fin_fetchAccountDetails(request, id):
    try:
        acc = Fin_Chart_Of_Account.objects.get(id=id)
        hist = Fin_ChartOfAccount_History.objects.filter(account=acc).last()
        his = None
        if hist:
            his = {
                "action": hist.action,
                "date": hist.date,
                "doneBy": hist.LoginDetails.First_name
                + " "
                + hist.LoginDetails.Last_name,
            }
        accSerializer = AccountsSerializer(acc)
        return Response(
            {
                "status": True,
                "account": accSerializer.data,
                "history": his,
            },
            status=status.HTTP_200_OK,
        )
    except Exception as e:
        print(e)
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

@api_view(("POST",))
def Fin_changeAccountStatus(request):
    try:
        acId = request.data["id"]
        data = Fin_Chart_Of_Account.objects.get(id=acId)
        data.status = request.data["status"]
        data.save()
        return Response({"status": True}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

@api_view(("DELETE",))
def Fin_deleteAccount(request, id):
    try:
        acc = Fin_Chart_Of_Account.objects.get(id=id)
        acc.delete()
        return Response({"status": True}, status=status.HTTP_200_OK)
    except Exception as e:
        print(e)
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

@api_view(("GET",))
def Fin_accountsPdf(request):
    try:
        id = request.GET['Id']
        acId = request.GET['ac_id']

        data = Fin_Login_Details.objects.get(id=id)
        if data.User_Type == "Company":
            com = Fin_Company_Details.objects.get(Login_Id=id)
        else:
            com = Fin_Staff_Details.objects.get(Login_Id=id).company_id

        acc = Fin_Chart_Of_Account.objects.get(id=acId)
        context = {'account': acc}
        
        template_path = 'company/Fin_Account_Transaction_Pdf.html'
        fname = 'Account_transactions_'+acc.account_name
        # Create a Django response object, and specify content_type as pdftemp_
        response = HttpResponse(content_type="application/pdf")
        response["Content-Disposition"] = f"attachment; filename = {fname}.pdf"
        # find the template and render it.
        template = get_template(template_path)
        html = template.render(context)

        # create a pdf
        pisa_status = pisa.CreatePDF(html, dest=response)
        # if error then show some funny view
        if pisa_status.err:
            return HttpResponse("We had some errors <pre>" + html + "</pre>")
        return response
    except Exception as e:
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

@api_view(("POST",))
def Fin_shareAccountTransactionsToEmail(request):
    try:
        id = request.data["Id"]
        data = Fin_Login_Details.objects.get(id=id)
        if data.User_Type == "Company":
            com = Fin_Company_Details.objects.get(Login_Id=id)
        else:
            com = Fin_Staff_Details.objects.get(Login_Id=id).company_id

        acId = request.data["ac_id"]
        acc = Fin_Chart_Of_Account.objects.get(id=acId)
        emails_string = request.data["email_ids"]

        # Split the string by commas and remove any leading or trailing whitespace
        emails_list = [email.strip() for email in emails_string.split(",")]
        email_message = request.data["email_message"]
        # print(emails_list)

        context = {'account': acc}
        template_path = 'company/Fin_Account_Transaction_Pdf.html'
        template = get_template(template_path)

        html = template.render(context)
        result = BytesIO()
        pdf = pisa.pisaDocument(BytesIO(html.encode("ISO-8859-1")), result)
        pdf = result.getvalue()
        filename = f'Account_transactions-{acc.account_name}.pdf'
        subject = f"Account_transactions_{acc.account_name}"
        email = EmailMessage(
            subject,
            f"Hi,\nPlease find the attached Transaction details - ACCOUNT-{acc.account_name}. \n{email_message}\n\n--\nRegards,\n{com.Company_name}\n{com.Address}\n{com.State} - {com.Country}\n{com.Contact}",
            from_email=settings.EMAIL_HOST_USER,
            to=emails_list,
        )
        email.attach(filename, pdf, "application/pdf")
        email.send(fail_silently=False)

        return Response({"status": True}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

@api_view(("GET",))
def Fin_fetchAccountHistory(request, id):
    try:
        acc = Fin_Chart_Of_Account.objects.get(id=id)
        hist = Fin_ChartOfAccount_History.objects.filter(account=acc)
        his = []
        if hist:
            for i in hist:
                h = {
                    "action": i.action,
                    "date": i.date,
                    "name": i.LoginDetails.First_name + " " + i.LoginDetails.Last_name,
                }
                his.append(h)
        accSerializer = AccountsSerializer(acc)
        return Response(
            {"status": True, "account": accSerializer.data, "history": his},
            status=status.HTTP_200_OK,
        )
    except Exception as e:
        print(e)
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

@api_view(("PUT",))
def Fin_updateAccount(request):
    try:
        s_id = request.data["Id"]
        acId = request.data['ac_id']
        acc = Fin_Chart_Of_Account.objects.get(id=acId)

        data = Fin_Login_Details.objects.get(id=s_id)
        if data.User_Type == "Company":
            com = Fin_Company_Details.objects.get(Login_Id=s_id)
        else:
            com = Fin_Staff_Details.objects.get(Login_Id=s_id).company_id

        request.data["parent_account"] = (
            request.data["parent_account"]
            if request.data["sub_account"] == True
            else None
        )
        request.data["bank_account_no"] = None if request.data["bank_account_no"] == "" else request.data["bank_account_no"]

        # save account and transaction if account doesn't exists already
        if acc.account_name != request.data['account_name'] and Fin_Chart_Of_Account.objects.filter(
            Company=com, account_name__iexact=request.data["account_name"]
        ).exists():
            return Response(
                {"status": False, "message": "Account Name already exists."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        else:
            serializer = AccountsSerializer(acc,data=request.data)
            if serializer.is_valid():
                serializer.save()
                # save transaction

                Fin_ChartOfAccount_History.objects.create(
                    Company=com,
                    LoginDetails=data,
                    account = acc,
                    action="Edited",
                )
                return Response(
                    {"status": True, "data": serializer.data}, status=status.HTTP_200_OK
                )
            else:
                return Response(
                    {"status": False, "data": serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST,
                )
    except Exception as e:
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
        
        
#Employee
@api_view(("GET",))
def Fin_createemployee(request, id):
    try:
        data = Fin_Login_Details.objects.get(id=id)
        if data.User_Type == 'Company':
            cmp = Fin_Company_Details.objects.get(Login_Id=id)
        else:
            cmp = Fin_Staff_Details.objects.get(Login_Id = id).company_id
        bloodgp = Employee_Blood_Group.objects.filter(company=cmp)
        serializer = EmployeeBloodgroupSerializer(bloodgp, many=True)
        return Response(
            {"status": True, "bloodgp": serializer.data}, status=status.HTTP_200_OK
        )
    except Exception as e:
        print(e)
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
        

@api_view(("POST",))
def Fin_createNewbloodgroup(request):
    try:
        s_id = request.data.get("Id")
        data = Fin_Login_Details.objects.get(id=s_id)
        print(data)
        blood_group = request.data.get("blood_group", "").upper()
        print(blood_group)
        if not blood_group:
            return Response(
                {"status": False, "message": "Blood group is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        invalid_groups = ['A+', 'A-', 'B+','B-','AB+','AB-', 'O+','O-']

        if blood_group in invalid_groups:
            return Response(
                {"status": False, "message": "Invalid blood group."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        
        if data.User_Type == "Company":
            com = Fin_Company_Details.objects.get(Login_Id=s_id)
        else:
            staff = Fin_Staff_Details.objects.get(Login_Id=s_id)
            com = staff.company_id
        
        request.data["Company"] = com.id
        if Employee_Blood_Group.objects.filter(company_id=com.id, blood_group=blood_group, login_id=s_id).exists():
            return Response(
                {"status": False, "message": "Blood group already exists."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = EmployeeBloodgroupSerializer(data=request.data)
        print(serializer)
        
        if serializer.is_valid():
            Employee_Blood_Group.objects.create(
                company=com,
                login=data,
                blood_group=serializer.validated_data['blood_group'].upper(),
            )
            print("yes")
            return Response(
                {"status": True, "data": serializer.data},
                status=status.HTTP_201_CREATED,
            )
        else:
            return Response(
                {"status": False, "data": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
    except Fin_Login_Details.DoesNotExist:
        return Response(
            {"status": False, "message": "Login details not found."},
            status=status.HTTP_404_NOT_FOUND,
        )
    except Fin_Company_Details.DoesNotExist:
        return Response(
            {"status": False, "message": "Company details not found."},
            status=status.HTTP_404_NOT_FOUND,
        )
    except Fin_Staff_Details.DoesNotExist:
        return Response(
            {"status": False, "message": "Staff details not found."},
            status=status.HTTP_404_NOT_FOUND,
        )
    except Exception as e:
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

@api_view(("POST",))
def employee_save(request):
    if request.method == 'POST':
        try:
            # Make a mutable copy of request data
            data = request.data.copy()
            
            s_id = data.get("Id")
            datauser = Fin_Login_Details.objects.get(id=s_id)
            
            if datauser.User_Type == "Company":
                com = Fin_Company_Details.objects.get(Login_Id=s_id)
            else:
                staff = Fin_Staff_Details.objects.get(Login_Id=s_id)
                com = staff.company_id
            
            data["Company"] = com.id
            
            file = request.FILES.get('file')
            image = request.FILES.get('image')
            account_number= data.get('Account_Number')
            ifsc=data.get('IFSC')
            name_of_bank=data.get('Bank_Name')
            branch_name=data.get('Branch_Name')
            bank_transaction_type=data.get('Transaction_Type')
            print(account_number)
            print(ifsc)
            print(branch_name)
            print(name_of_bank)
            print(bank_transaction_type)
            provide_bank_details=data.get('Bank_Details')
            print(provide_bank_details)
            tds_applicable=data.get('TDS_Applicable')
            tds_type=data.get('TDS_Type')
            percentage_amount=data.get('TDS_Amount')
            percentage_amount2=data.get('TDS_Percentage')

            print(tds_applicable)
            print(tds_type)
            print(percentage_amount)
            print(percentage_amount2)


            present_address = json.loads(data.get('Present_Address'))
            permanent_address = json.loads(data.get('Permanent_Address'))
            salary_amount = data.get('Salary_Amount')
            if tds_type == 'Percentage':
                percentage_amount = data.get('TDS_Percentage')
            else:
                percentage_amount = data.get('TDS_Amount')
            if not salary_amount:
                salary_amount = None

            # Handling amount per hour
            amount_per_hour = data.get('Amount_Per_Hour')
            if not amount_per_hour or amount_per_hour == '0':
                amount_per_hour = 0

            # Handling working hours
            working_hours = data.get('Working_Hours')
            if not working_hours or working_hours == '0':
                working_hours = 0


            # Example of setting multiple fields from data
            employee_data = {
                "company": com,
                "login": datauser,
                "title": data.get('Title'),
                "first_name": data.get('First_Name'),
                "last_name": data.get('Last_Name'),
                "date_of_joining": data.get('Joining_Date'),
                "salary_effective_from": data.get('Salary_Date'),
                "employee_salary_type": data.get('Salary_Type'),
                "salary_amount": data.get('Salary_Amount'),
                "amount_per_hour": data.get('Amount_Per_Hour'),
                "total_working_hours": data.get('Working_Hours'),
                "alias": data.get('Alias'),
                "employee_number": data.get('Employee_Number'),
                "employee_designation": data.get('Designation'),
                "employee_current_location": data.get('Location'),
                "gender": data.get('Gender'),
                "date_of_birth": data.get('DOB'),
                "age": data.get('Age'),
                "blood_group": data.get('Blood_Group'),
                "mobile": data.get('Contact_Number'),
                "emergency_contact": data.get('Emergency_Contact_Number'),
                "employee_mail": data.get('Personal_Email'),
                "fathers_name_mothers_name": data.get('Parent_Name'),
                "spouse_name": data.get('Spouse_Name'),
                "upload_file": file,
                "provide_bank_details": data.get('Bank_Details'),
                "tds_applicable": data.get('TDS_Applicable'),
                "account_number": data.get('Account_Number'),
                "ifsc": data.get('IFSC'),
                "name_of_bank": data.get('Bank_Name'),
                "branch_name": data.get('Branch_Name'),
                "bank_transaction_type": data.get('Transaction_Type'),
                "tds_type": data.get('TDS_Type'),
                "percentage_amount": percentage_amount,
                "street": present_address.get('address'),
                "city": present_address.get('city'),
                "state": present_address.get('state'),
                "pincode": present_address.get('pincode'),
                "country": present_address.get('country'),
                "temporary_street": permanent_address.get('address'),
                "temporary_city": permanent_address.get('city'),
                "temporary_state": permanent_address.get('state'),
                "temporary_pincode": permanent_address.get('pincode'),
                "temporary_country": permanent_address.get('country'),
                "pan_number": data.get('PAN'),
                "income_tax_number": data.get('Income_Tax'),
                "aadhar_number": data.get('Aadhar'),
                "universal_account_number": data.get('UAN'),
                "pf_account_number": data.get('PF'),
                "pr_account_number": data.get('PR'),
                "upload_image": image,
                "employee_status": 'Active',
            }
            A=employee_data["provide_bank_details"]
            print(A)
            if Employee.objects.filter(employee_mail=employee_data["employee_mail"], mobile=employee_data["mobile"], employee_number=employee_data["employee_number"], company=com).exists():
                return JsonResponse({"status": False, "message": "User already exists"})
            elif Employee.objects.filter(mobile=employee_data["mobile"], company_id=com.id).exists():
                return JsonResponse({"status": False, "message": "Phone number already exists"})
            elif Employee.objects.filter(emergency_contact=employee_data["emergency_contact"], company_id=com.id).exists():
                return JsonResponse({"status": False, "message": "Emergency phone number already exists"})
            elif Employee.objects.filter(employee_mail=employee_data["employee_mail"], company_id=com.id).exists():
                return JsonResponse({"status": False, "message": "Email already exists"})
            elif Employee.objects.filter(employee_number=employee_data["employee_number"], company_id=com.id).exists():
                return JsonResponse({"status": False, "message": "Employee ID already exists"})
            elif employee_data["income_tax_number"] and Employee.objects.filter(income_tax_number=employee_data["income_tax_number"], company_id=com.id).exists():
                return JsonResponse({"status": False, "message": "Income Tax Number already exists"})
            elif employee_data["pf_account_number"] and Employee.objects.filter(pf_account_number=employee_data["pf_account_number"], company_id=com.id).exists():
                return JsonResponse({"status": False, "message": "PF account number already exists"})
            elif employee_data["aadhar_number"] and Employee.objects.filter(aadhar_number=employee_data["aadhar_number"], company_id=com.id).exists():
                return JsonResponse({"status": False, "message": "Aadhar number already exists"})
            elif employee_data["pan_number"] and Employee.objects.filter(pan_number=employee_data["pan_number"], company_id=com.id).exists():
                return JsonResponse({"status": False, "message": "PAN number already exists"})
            elif employee_data["universal_account_number"] and Employee.objects.filter(universal_account_number=employee_data["universal_account_number"], company_id=com.id).exists():
                return JsonResponse({"status": False, "message": "Universal account number already exists"})
            elif employee_data["pr_account_number"] and Employee.objects.filter(pr_account_number=employee_data["pr_account_number"], company_id=com.id).exists():
                return JsonResponse({"status": False, "message": "PR account number already exists"})
            
            else:
                employee = Employee(**employee_data)
                employee.save()

                history = Employee_History(
                    company=com,
                    login=datauser,
                    employee=employee,
                    date=date.today(),
                    action='Created'
                )
                history.save()
                return Response(
                    {"status": True, 'message': 'Employee saved successfully.'}, status=status.HTTP_200_OK
                )
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    else:
        return JsonResponse({'error': 'Invalid request method.'}, status=405)


@api_view(("GET",))
def Fin_fetchemployee(request, id):
    try:
        data = Fin_Login_Details.objects.get(id=id)
        if data.User_Type == "Company":
            com = Fin_Company_Details.objects.get(Login_Id=id)
        else:
            com = Fin_Staff_Details.objects.get(Login_Id=id).company_id

        items = Employee.objects.filter(company=com)
        serializer = EmployeeSerializer(items, many=True)
        return Response(
            {"status": True, "items": serializer.data}, status=status.HTTP_200_OK
        )
    except Exception as e:
        print(e)
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

@api_view(("GET",))
def Fin_fetchEmployeeDetails(request, id):
    try:
        item = Employee.objects.get(id=id)
        hist = Employee_History.objects.filter(employee=item).last()
        print(hist)
        his = None
        if hist:
            his = {
                "action": hist.action,
                "date": hist.date,
                "doneBy": hist.login.First_name
                + " "
                + hist.login.Last_name,
            }
        cmt = Employee_Comment.objects.filter(employee=item)
        itemSerializer = EmployeeSerializer(item)
        commentsSerializer = EmployeeCommentsSerializer(cmt, many=True)
        return Response(
            {
                "status": True,
                "item": itemSerializer.data,
                "history": his,
                "comments": commentsSerializer.data,
            },
            status=status.HTTP_200_OK,
        )
    except Exception as e:
        print(e)
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(("POST",))
def Fin_changeEmployeeStatus(request):
    try:
        itemId = request.data["id"]
        data = Employee.objects.get(id=itemId)
        S=request.data["status"]
        data.employee_status = request.data["status"]
        print(S)
        data.save()
        return Response({"status": True}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
      

@api_view(("POST",))
def Fin_addEmployeeComment(request):
    try:
        id = request.data.get("Id")  # Retrieve 'Id' from request data
        data = Fin_Login_Details.objects.get(id=id)
        if data.User_Type == "Company":
            com = Fin_Company_Details.objects.get(Login_Id=id)
        else:
            com = Fin_Staff_Details.objects.get(Login_Id=id).company_id

        # Prepare the data for the serializer
        serializer_data = {
            "comment": request.data.get("comments"),
            "employee": request.data.get("item"),  # Ensure this matches the serializer field
            "company": com.id,
            "login": data.id,
            # You can add 'date' or other fields if required
        }

        serializer = EmployeeCommentsSerializer(data=serializer_data)
        print(serializer)
        if serializer.is_valid():
            Employee_Comment.objects.create(
                company=com,
                login=data,
                comment=serializer.validated_data['comment'],
                employee=serializer.validated_data['employee'],  # Ensure this matches the model field
            )
            print("yes")
            return Response(
                {"status": True, "data": serializer.data},
                status=status.HTTP_201_CREATED,
            )
        else:
            return Response(
                {"status": False, "message": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
    except Fin_Login_Details.DoesNotExist:
        return Response(
            {"status": False, "message": "Login details not found"},
            status=status.HTTP_404_NOT_FOUND,
        )
    except Fin_Company_Details.DoesNotExist:
        return Response(
            {"status": False, "message": "Company details not found"},
            status=status.HTTP_404_NOT_FOUND,
        )
    except Fin_Staff_Details.DoesNotExist:
        return Response(
            {"status": False, "message": "Staff details not found"},
            status=status.HTTP_404_NOT_FOUND,
        )
    except Exception as e:
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
@api_view(("DELETE",))
def Fin_deleteemployee(request, id):
    try:
        item = Employee.objects.get(id=id)
        item.delete()
        return Response({"status": True}, status=status.HTTP_200_OK)
    except Exception as e:
        print(e)
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(("DELETE",))
def Fin_deleteemployeeComment(request, id):
    try:
        cmt = Employee_Comment.objects.get(id=id)
        cmt.delete()
        return Response({"status": True}, status=status.HTTP_200_OK)
    except Exception as e:
        print(e)
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(("GET",))
def Fin_fetchemployeeHistory(request, id):
    try:
        item = Employee.objects.get(id=id)
        hist = Employee_History.objects.filter(employee=item)
        print(item)
        print(hist)
        
        his = []
        if hist:
            for i in hist:
                h = {
                    "action": i.action,
                    "date": i.date,
                    "name": i.login.First_name + " " + i.login.Last_name,
                }
                his.append(h)
        itemSerializer = EmployeeSerializer(item)
        return Response(
            {"status": True, "item": itemSerializer.data, "history": his},
            status=status.HTTP_200_OK,
        )
    except Exception as e:
        print(e)
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )



@api_view(("GET",))
def Fin_employTransactionPdf(request, itemId, id):
    try:
        data = Fin_Login_Details.objects.get(id=id)
        if data.User_Type == "Company":
            com = Fin_Company_Details.objects.get(Login_Id=id)
        else:
            com = Fin_Staff_Details.objects.get(Login_Id=id).company_id

        item = Employee.objects.get(id=itemId)
        context = {"employ": item}

        template_path = "company/Fin_employee_pdf.html"
        fname = f"Employee_{item.id}"  # You might want to append the item ID to the filename

        response = HttpResponse(content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="{fname}.pdf"'

        template = get_template(template_path)
        html = template.render(context)

        pisa_status = pisa.CreatePDF(html, dest=response)
        if pisa_status.err:
            return HttpResponse(f"We had some errors <pre>{html}</pre>")

        return response

    except Fin_Login_Details.DoesNotExist:
        return HttpResponse("Login details not found.", status=404)
    except Fin_Company_Details.DoesNotExist:
        return HttpResponse("Company details not found.", status=404)
    except Fin_Staff_Details.DoesNotExist:
        return HttpResponse("Staff details not found.", status=404)
    except Employee.DoesNotExist:
        return HttpResponse("Employee not found.", status=404)
    except Exception as e:
        return HttpResponse(f"An unexpected error occurred: {str(e)}", status=500)


@api_view(("POST",))
def Fin_share_employ_TransactionsToEmail(request):
    try:
        id = request.data["Id"]
        data = Fin_Login_Details.objects.get(id=id)
        if data.User_Type == "Company":
            com = Fin_Company_Details.objects.get(Login_Id=id)
        else:
            com = Fin_Staff_Details.objects.get(Login_Id=id).company_id

        itemId = request.data["itemId"]
        item = Employee.objects.get(id=itemId)
        emails_string = request.data["email_ids"]

        # Split the string by commas and remove any leading or trailing whitespace
        emails_list = [email.strip() for email in emails_string.split(",")]
        email_message = request.data["email_message"]
        # print(emails_list)

        

        context = {"employ": item}
        template_path = "company/Fin_employee_pdf.html"
        template = get_template(template_path)

        html = template.render(context)
        result = BytesIO()
        pdf = pisa.pisaDocument(BytesIO(html.encode("ISO-8859-1")), result)
        pdf = result.getvalue()
        filename = f"Employee-{item.first_name}.pdf"
        subject = f"Employee_{item.first_name}"
        email = EmailMessage(
            subject,
            f"Hi,\nPlease find the attached Transaction details - Employee-{item.first_name}. \n{email_message}\n\n--\nRegards,\n{com.Company_name}\n{com.Address}\n{com.State} - {com.Country}\n{com.Contact}",
            from_email=settings.EMAIL_HOST_USER,
            to=emails_list,
        )
        email.attach(filename, pdf, "application/pdf")
        email.send(fail_silently=False)

        return Response({"status": True}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["PUT"])
def Fin_updateemployee(request):
    try:
        s_id = request.data["Id"]
        data = Fin_Login_Details.objects.get(id=s_id)

        if data.User_Type == "Company":
            com = Fin_Company_Details.objects.get(Login_Id=s_id)
        else:
            com = Fin_Staff_Details.objects.get(Login_Id=s_id).company_id
        
        employee = Employee.objects.get(id=request.data['itemId'])

        account_number = request.data['Account_Number']
        ifsc = request.data['IFSC']
        name_of_bank = request.data['Bank_Name']
        branch_name = request.data['Branch_Name']
        bank_transaction_type = request.data['Transaction_Type']
        provide_bank_details = request.data['Bank_Details']
        tds_applicable = request.data['TDS_Applicable']
        tds_type = request.data['TDS_Type']
        percentage_amount = request.data['TDS_Amount']
        percentage_amount2 = request.data['TDS_Percentage']

        present_address = json.loads(request.data['Present_Address'])
        permanent_address = json.loads(request.data['Permanent_Address'])
        salary_amount = request.data['Salary_Amount']
        if tds_type == 'Percentage':
            percentage_amount = request.data['TDS_Percentage']
        else:
            percentage_amount = request.data['TDS_Amount']
        if not salary_amount:
            salary_amount = None

        # Handling amount per hour
        amount_per_hour = request.data['Amount_Per_Hour']
        if not amount_per_hour or amount_per_hour == '0':
            amount_per_hour = 0

        # Handling working hours
        working_hours = request.data.get('Working_Hours')
        if not working_hours or working_hours == '0':
            working_hours = 0

        # Extract fields from request data
        employee_data = {
            "company": com,
            "login": data,
            "title": request.data['Title'],
            "first_name": request.data['First_Name'],
            "last_name": request.data['Last_Name'],
            "date_of_joining": request.data['Joining_Date'],
            "salary_effective_from": request.data['Salary_Date'],
            "employee_salary_type": request.data['Salary_Type'],
            "salary_amount": request.data['Salary_Amount'],
            "amount_per_hour": request.data['Amount_Per_Hour'],
            "total_working_hours": request.data['Working_Hours'],
            "alias": request.data['Alias'],
            "employee_number": request.data['Employee_Number'],
            "employee_designation": request.data['Designation'],
            "employee_current_location": request.data['Location'],
            "gender": request.data['Gender'],
            "date_of_birth": request.data['DOB'],
            "age": request.data['Age'],
            "blood_group": request.data['Blood_Group'],
            "mobile": request.data['Contact_Number'],
            "emergency_contact": request.data['Emergency_Contact_Number'],
            "employee_mail": request.data['Personal_Email'],
            "fathers_name_mothers_name": request.data['Parent_Name'],
            "spouse_name": request.data['Spouse_Name'],
            "provide_bank_details": request.data['Bank_Details'],
            "tds_applicable": request.data['TDS_Applicable'],
            "account_number": request.data['Account_Number'],
            "ifsc": request.data['IFSC'],
            "name_of_bank": request.data['Bank_Name'],
            "branch_name": request.data['Branch_Name'],
            "bank_transaction_type": request.data['Transaction_Type'],
            "tds_type": request.data['TDS_Type'],
            "percentage_amount": percentage_amount,
            "street": present_address.get('address'),
            "city": present_address.get('city'),
            "state": present_address.get('state'),
            "pincode": present_address.get('pincode'),
            "country": present_address.get('country'),
            "temporary_street": permanent_address.get('address'),
            "temporary_city": permanent_address.get('city'),
            "temporary_state": permanent_address.get('state'),
            "temporary_pincode": permanent_address.get('pincode'),
            "temporary_country": permanent_address.get('country'),
            "pan_number": request.data['PAN'],
            "income_tax_number": request.data['Income_Tax'],
            "aadhar_number": request.data['Aadhar'],
            "universal_account_number": request.data['UAN'],
            "pf_account_number": request.data['PF'],
            "pr_account_number": request.data['PR'],
            "employee_status": 'Active',
        }

        # Handle file uploads
        if 'file' in request.FILES:
            employee.upload_file = request.FILES['file']
        if 'image' in request.FILES:
            employee.upload_image = request.FILES['image']

        # Uniqueness checks
        emp = Employee.objects.exclude(id=employee.id).filter(company_id=com.id)
        
        if emp.filter(mobile=employee_data['mobile']).exists():
            return JsonResponse({"status": False, "message": "Phone number already exists"})
        elif emp.filter(emergency_contact=employee_data['emergency_contact']).exists():
            return JsonResponse({"status": False, "message": "Emergency contact number already exists"})
        elif emp.filter(employee_mail=employee_data['employee_mail']).exists():
            return JsonResponse({"status": False, "message": "Email already exists"})
        elif emp.filter(employee_number=employee_data['employee_number']).exists():
            return JsonResponse({"status": False, "message": "Employee ID already exists"})
        elif employee_data['income_tax_number'] and emp.filter(income_tax_number=employee_data['income_tax_number']).exists():
            return JsonResponse({"status": False, "message": "Income Tax Number already exists"})
        elif employee_data['pf_account_number'] and emp.filter(pf_account_number=employee_data['pf_account_number']).exists():
            return JsonResponse({"status": False, "message": "PF account number already exists"})
        elif employee_data['aadhar_number'] and emp.filter(aadhar_number=employee_data['aadhar_number']).exists():
            return JsonResponse({"status": False, "message": "Aadhar number already exists"})
        elif employee_data['pan_number'] and emp.filter(pan_number=employee_data['pan_number']).exists():
            return JsonResponse({"status": False, "message": "PAN number already exists"})
        elif employee_data['universal_account_number'] and emp.filter(universal_account_number=employee_data['universal_account_number']).exists():
            return JsonResponse({"status": False, "message": "Universal account number already exists"})

        # Update employee fields
        for key, value in employee_data.items():
            setattr(employee, key, value)

        employee.save()
        
        history = Employee_History(
            company=com,
            employee=employee,
            login=data,
            date=date.today(),
            action='Edited'
        )
        history.save()

        return Response({"status": True, "message": "Employee updated successfully"}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
#End

# Stock Adjustment

@api_view(("GET",))
def Fin_fetchStockAdjust(request, id):
    try:
        data = Fin_Login_Details.objects.get(id=id)
        if data.User_Type == "Company":
            com = Fin_Company_Details.objects.get(Login_Id=id)
        else:
            com = Fin_Staff_Details.objects.get(Login_Id=id).company_id

        stock = Stock_Adjustment.objects.filter(company = com)
        serializer = StockAdjustSerializer(stock, many=True)
        return Response(
            {"status": True, "stock": serializer.data}, status=status.HTTP_200_OK
        )
    except Exception as e:
        print(e)
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

@api_view(("GET",))
def Fin_getStockReasons(request, id):
    try:
        data = Fin_Login_Details.objects.get(id=id)
        if data.User_Type == 'Company':
            cmp = Fin_Company_Details.objects.get(Login_Id=id)
        else:
            cmp = Fin_Staff_Details.objects.get(Login_Id = id).company_id
        rsn = Stock_Reason.objects.filter(company=cmp)
        serializer = StockReasonSerializer(rsn, many=True)
        return Response(
            {"status": True, "reason": serializer.data}, status=status.HTTP_200_OK
        )
    except Exception as e:
        print(e)
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

@api_view(("POST",))
def Fin_createNewReason(request):
    try:
        s_id = request.data["Id"]
        data = Fin_Login_Details.objects.get(id=s_id)
        if data.User_Type == "Company":
            com = Fin_Company_Details.objects.get(Login_Id=s_id)
        else:
            com = Fin_Staff_Details.objects.get(Login_Id=s_id).company_id
        request.data["company"] = com.id
        request.data['login_details'] = data.id

        serializer = StockReasonSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"status": True, "data": serializer.data},
                status=status.HTTP_201_CREATED,
            )
        else:
            return Response(
                {"status": False, "data": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
    except Exception as e:
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

@api_view(("GET",))
def Fin_getStockAdjustAccounts(request, id):
    try:
        data = Fin_Login_Details.objects.get(id=id)
        if data.User_Type == 'Company':
            cmp = Fin_Company_Details.objects.get(Login_Id=id)
        else:
            cmp = Fin_Staff_Details.objects.get(Login_Id = id).company_id
        bnk = Fin_Chart_Of_Account.objects.filter(account_type="Bank", Company=cmp).order_by("account_name")
        csh = Fin_Chart_Of_Account.objects.filter(account_type="Cash", Company=cmp).order_by("account_name")
        cc = Fin_Chart_Of_Account.objects.filter(account_type="Credit Card", Company=cmp).order_by("account_name")
        pc = Fin_Chart_Of_Account.objects.filter(account_type="Payment Clearing Account", Company=cmp).order_by("account_name")
        bnkSerializer = AccountsSerializer(bnk, many=True)
        cshSerializer = AccountsSerializer(csh, many=True)
        ccSerializer = AccountsSerializer(cc, many=True)
        pcSerializer = AccountsSerializer(pc, many=True)
        return Response(
            {"status": True, "bank": bnkSerializer.data, "cash": cshSerializer.data, "credit": ccSerializer.data, 'payment': pcSerializer.data}, status=status.HTTP_200_OK
        )
    except Exception as e:
        print(e)
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

@api_view(("GET",))
def Fin_getStockAdjustRefNo(request, id):
    try:
        data = Fin_Login_Details.objects.get(id=id)
        if data.User_Type == 'Company':
            cmp = Fin_Company_Details.objects.get(Login_Id=id)
        else:
            cmp = Fin_Staff_Details.objects.get(Login_Id = id).company_id
        
        latest_sa = Stock_Adjustment.objects.filter(company = cmp).order_by('-id').first()
        new_number = int(latest_sa.reference_no) + 1 if latest_sa else 1

        if Stock_Adjustment_RefNo.objects.filter(company = cmp).exists():
            deleted = Stock_Adjustment_RefNo.objects.get(company = cmp)
            
            if deleted:
                while int(deleted.reference_no) >= new_number:
                    new_number+=1
        return Response(
            {"status": True, "refNo": new_number}, status=status.HTTP_200_OK
        )
    except Exception as e:
        print(e)
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

@api_view(("GET",))
def Fin_getItemQuantityData(request):
    try:
        s_id = request.GET["Id"]
        data = Fin_Login_Details.objects.get(id=s_id)
        if data.User_Type == 'Company':
            cmp = Fin_Company_Details.objects.get(Login_Id=s_id)
        else:
            cmp = Fin_Staff_Details.objects.get(Login_Id = s_id).company_id
        
        item = Fin_Items.objects.get(Company = cmp, name = request.GET['name'])
        try:
            stock = item.current_stock
        except:
            stock = 0
        return Response(
            {"status": True, "stock": stock}, status=status.HTTP_200_OK
        )
    except Exception as e:
        print(e)
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

@api_view(("GET",))
def Fin_getItemValueData(request):
    try:
        s_id = request.GET["Id"]
        data = Fin_Login_Details.objects.get(id=s_id)
        if data.User_Type == 'Company':
            cmp = Fin_Company_Details.objects.get(Login_Id=s_id)
        else:
            cmp = Fin_Staff_Details.objects.get(Login_Id = s_id).company_id
        
        item = Fin_Items.objects.get(Company = cmp, name = request.GET['name'])
        try:
            stock = item.current_stock
            p = item.purchase_price
            value = stock * p
        except:
            value = 0
        return Response(
            {"status": True, "value": value}, status=status.HTTP_200_OK
        )
    except Exception as e:
        print(e)
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

from copy import deepcopy
@api_view(("POST",))
@parser_classes((MultiPartParser, FormParser))
def Fin_createNewStockAdjust(request):
    try:
        s_id = request.data["Id"]
        data = Fin_Login_Details.objects.get(id=s_id)
        if data.User_Type == "Company":
            com = Fin_Company_Details.objects.get(Login_Id=s_id)
        else:
            com = Fin_Staff_Details.objects.get(Login_Id=s_id).company_id

        # Make a mutable copy of request.data
        mutable_data = deepcopy(request.data)
        mutable_data["company"] = com.id
        mutable_data["login_details"] = com.Login_Id.id

        # Parse stock_items from JSON
        stockItems = json.loads(request.data['stock_items'])

        serializer = StockAdjustSerializer(data=mutable_data, partial=True)
        if serializer.is_valid():
            serializer.save()
            stock = Stock_Adjustment.objects.get(id=serializer.data['id'])

            if request.data['mode_of_adjustment'] == 'Quantity':
                for i in stockItems:
                    item_instance = Fin_Items.objects.get(name=i.get('item'), Company=com)

                    if float(i.get('quantityInHand')) > float(i.get('quantity')):
                        diff = float(i.get('quantity')) + float(i.get('difference'))
                        item_instance.current_stock = diff
                    else:
                        diff = float(i.get('quantity')) + float(i.get('difference'))
                        item_instance.current_stock = diff
                    item_instance.save()

                    Stock_Adjustment_Items.objects.create(
                        item=item_instance,
                        quantity_avail=i.get('quantity'),
                        quantity_inhand=i.get('quantityInHand'),
                        quantity_adj=i.get('difference'),
                        stock_adjustment=stock,
                        company=com,
                        type="Quantity",
                        login_details=data   
                    )
                    
                    Stock_Adjustment_History.objects.create(
                        company=com,
                        login_details=data,
                        item=item_instance,
                        date=request.data.get('adjusting_date'),
                        action='Created',
                        stock_adjustment=stock
                    )
            elif request.data['mode_of_adjustment'] == 'Value':
                for i in stockItems:
                    item_instance = Fin_Items.objects.get(name=i.get('item'), Company=com)

                    Stock_Adjustment_Items.objects.create(
                        item=item_instance,
                        current_val = i.get('value'),
                        changed_val = i.get('changedValue'),
                        adjusted_val = i.get('difference'),
                        company=com,
                        login_details=data,
                        stock_adjustment=stock,
                        type='Value'
                    )

                    Stock_Adjustment_History.objects.create(
                        company=com,
                        login_details=data,
                        item=item_instance,
                        date=request.data.get('adjusting_date'),
                        action='Created',
                        stock_adjustment=stock
                    )
            else:
                pass
            
            return Response(
                {"status": True, "data": serializer.data}, status=status.HTTP_200_OK
            )
        else:
            return Response(
                {"status": False, "data": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
    except Exception as e:
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

@api_view(("GET",))
def Fin_fetchStockAdjustDetails(request, id):
    try:
        stk = Stock_Adjustment.objects.get(id=id)
        hist = Stock_Adjustment_History.objects.filter(stock_adjustment=stk).last()
        his = None
        if hist:
            his = {
                "action": hist.action,
                "date": hist.date,
                "doneBy": hist.login_details.First_name
                + " "
                + hist.login_details.Last_name,
            }
        cmt = Stock_Adjustment_Comment.objects.filter(stock_adjustment=stk)
        itms = Stock_Adjustment_Items.objects.filter(stock_adjustment=stk)
        statementDet = {
            "name": stk.login_details.First_name,
            "company": stk.company.Company_name,
            "pincode": stk.company.Pincode,
            "city": stk.company.City,
            "email": stk.company.Email,
            "state": stk.company.State,
        }
        items = []
        for i in itms:
            obj = {
                "id":i.id,
                'name': i.item.name,
                "quantity_avail": i.quantity_avail,
                "quantity_inhand": i.quantity_inhand,
                "quantity_adj": i.quantity_adj,
                "current_val": i.current_val,
                "changed_val": i.changed_val,
                "adjusted_val": i.adjusted_val
            }
            items.append(obj)
        stockSerializer = StockAdjustSerializer(stk)
        commentsSerializer = StockAdjustCommentSerializer(cmt, many=True)
        return Response(
            {
                "status": True,
                "stock": stockSerializer.data,
                "history": his,
                "comments": commentsSerializer.data,
                "items": items,
                "statement": statementDet,
            },
            status=status.HTTP_200_OK,
        )
    except Exception as e:
        print(e)
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

@api_view(("POST",))
def Fin_changeStockAdjustStatus(request):
    try:
        stkId = request.data["id"]
        data = Stock_Adjustment.objects.get(id=stkId)
        data.status = "Save"
        data.save()
        return Response({"status": True}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

@api_view(("POST",))
def Fin_addStockAdjustComment(request):
    try:
        id = request.data["Id"]
        data = Fin_Login_Details.objects.get(id=id)
        if data.User_Type == "Company":
            com = Fin_Company_Details.objects.get(Login_Id=id)
        else:
            com = Fin_Staff_Details.objects.get(Login_Id=id).company_id

        request.data["company"] = com.id
        request.data["login_details"] = data.id
        serializer = StockAdjustCommentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"status": True, "data": serializer.data}, status=status.HTTP_200_OK
            )
        else:
            return Response(
                {"status": False, "data": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
    except Exception as e:
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

@api_view(("DELETE",))
def Fin_deleteStockAdjustComment(request, id):
    try:
        cmt = Stock_Adjustment_Comment.objects.get(id=id)
        cmt.delete()
        return Response({"status": True}, status=status.HTTP_200_OK)
    except Exception as e:
        print(e)
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

@api_view(("GET",))
def Fin_fetchStockAdjustHistory(request, id):
    try:
        stk = Stock_Adjustment.objects.get(id=id)
        hist = Stock_Adjustment_History.objects.filter(stock_adjustment=stk)
        his = []
        if hist:
            for i in hist:
                h = {
                    "action": i.action,
                    "date": i.date,
                    "name": i.login_details.First_name + " " + i.login_details.Last_name,
                }
                his.append(h)
        stkSerializer = StockAdjustSerializer(stk)
        return Response(
            {"status": True, "stock": stkSerializer.data, "history": his},
            status=status.HTTP_200_OK,
        )
    except Exception as e:
        print(e)
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

@api_view(("DELETE",))
def Fin_deleteStockAdjust(request, id):
    try:
        stock = Stock_Adjustment.objects.get(id=id)
        com = stock.company
        # Storing ref number to deleted table
        # if entry exists and lesser than the current, update and save => Only one entry per company
        if Stock_Adjustment_RefNo.objects.filter(company = com).exists():
            deleted = Stock_Adjustment_RefNo.objects.get(company = com)
            if int(stock.reference_no) > int(deleted.reference_no):
                deleted.reference_no = stock.reference_no
                deleted.save()
        else:
            Stock_Adjustment_RefNo.objects.create(company = com, reference_no = stock.reference_no)

        stock.delete()
        return Response({"status": True}, status=status.HTTP_200_OK)
    except Exception as e:
        print(e)
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

@api_view(("GET",))
def Fin_stockAdjustStatementPdf(request):
    try:
        id = request.GET['Id']
        stockId = request.GET['stock_id']

        data = Fin_Login_Details.objects.get(id=id)
        if data.User_Type == "Company":
            com = Fin_Company_Details.objects.get(Login_Id=data.id)
        else:
            com = Fin_Staff_Details.objects.get(Login_Id=data.id).company_id

        stk = Stock_Adjustment.objects.get(id=stockId)
        itms = Stock_Adjustment_Items.objects.filter(stock_adjustment=stk)
        context = {'stocks': stk, 'st_items':itms, 'com':com}

        template_path = 'company/Fin_StockAdjustment_Pdf.html'
        fname = 'StockAdjust_Statement'+ str(stk.reference_no)
        # Create a Django response object, and specify content_type as pdftemp_
        response = HttpResponse(content_type="application/pdf")
        response["Content-Disposition"] = f"attachment; filename = {fname}.pdf"
        # find the template and render it.
        template = get_template(template_path)
        html = template.render(context)

        # create a pdf
        pisa_status = pisa.CreatePDF(html, dest=response)
        # if error then show some funny view
        if pisa_status.err:
            return HttpResponse("We had some errors <pre>" + html + "</pre>")
        return response
    except Exception as e:
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

@api_view(("POST",))
def Fin_shareStockAdjustStatementToEmail(request):
    try:
        id = request.data["Id"]
        data = Fin_Login_Details.objects.get(id=id)
        if data.User_Type == "Company":
            com = Fin_Company_Details.objects.get(Login_Id=data.id)
        else:
            com = Fin_Staff_Details.objects.get(Login_Id=data.id).company_id

        stockId = request.data["stock_id"]

        emails_string = request.data["email_ids"]

        # Split the string by commas and remove any leading or trailing whitespace
        emails_list = [email.strip() for email in emails_string.split(",")]
        email_message = request.data["email_message"]
        # print(emails_list)

        stk = Stock_Adjustment.objects.get(id=stockId)
        itms = Stock_Adjustment_Items.objects.filter(stock_adjustment=stk)
        context = {'stocks': stk, 'st_items':itms, 'com':com}
        
        template_path = 'company/Fin_StockAdjustment_Pdf.html'
        template = get_template(template_path)

        html = template.render(context)
        result = BytesIO()
        pdf = pisa.pisaDocument(BytesIO(html.encode("ISO-8859-1")), result)
        pdf = result.getvalue()
        filename = f'StockAdjust_Statement_{stk.reference_no}.pdf'
        subject = f"StockAdjust_Statement_{stk.reference_no}"
        email = EmailMessage(
            subject,
            f"Hi,\nPlease find the attached details - STOCK ADJUST STATEMENT-{stk.reference_no}. \n{email_message}\n\n--\nRegards,\n{com.Company_name}\n{com.Address}\n{com.State} - {com.Country}\n{com.Contact}",
            from_email=settings.EMAIL_HOST_USER,
            to=emails_list,
        )
        email.attach(filename, pdf, "application/pdf")
        email.send(fail_silently=False)

        return Response({"status": True}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

@api_view(("POST",))
@parser_classes((MultiPartParser, FormParser))
def Fin_addStockAdjustAttachment(request):
    try:
        s_id = request.data["Id"]
        data = Fin_Login_Details.objects.get(id=s_id)
        if data.User_Type == "Company":
            com = Fin_Company_Details.objects.get(Login_Id=s_id)
        else:
            com = Fin_Staff_Details.objects.get(Login_Id=s_id).company_id

        stockId = request.data['stock_id']
        stock = Stock_Adjustment.objects.get(id=stockId)
        if request.data['attach_file']:
            stock.attach_file = request.data['attach_file']
        stock.save()
        return Response(
            {"status": True}, status=status.HTTP_200_OK
        )
    except Exception as e:
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

@api_view(("PUT",))
@parser_classes((MultiPartParser, FormParser))
def Fin_updateStockAdjust(request):
    try:
        s_id = request.data["Id"]
        stockID = request.data['stock_id']
        data = Fin_Login_Details.objects.get(id=s_id)
        if data.User_Type == "Company":
            com = Fin_Company_Details.objects.get(Login_Id=s_id)
        else:
            com = Fin_Staff_Details.objects.get(Login_Id=s_id).company_id

        # Make a mutable copy of request.data
        mutable_data = deepcopy(request.data)
        mutable_data["company"] = com.id
        mutable_data["login_details"] = com.Login_Id.id
        
        stock = Stock_Adjustment.objects.get(id=stockID)
        # Parse stock_items from JSON
        stockItems = json.loads(request.data['stock_items'])

        serializer = StockAdjustSerializer(stock,data=mutable_data, partial=True)
        if serializer.is_valid():
            serializer.save()

            Stock_Adjustment_Items.objects.filter(stock_adjustment = stock).delete()

            if request.data['mode_of_adjustment'] == 'Quantity':
                for i in stockItems:
                    item_instance = Fin_Items.objects.get(name=i.get('item'), Company=com)

                    if float(i.get('quantityInHand')) > float(i.get('quantity')):
                        diff = float(i.get('quantity')) + float(i.get('difference'))
                        item_instance.current_stock = diff
                    else:
                        diff = float(i.get('quantity')) + float(i.get('difference'))
                        item_instance.current_stock = diff
                    item_instance.save()

                    Stock_Adjustment_Items.objects.create(
                        item=item_instance,
                        quantity_avail=i.get('quantity'),
                        quantity_inhand=i.get('quantityInHand'),
                        quantity_adj=i.get('difference'),
                        stock_adjustment=stock,
                        company=com,
                        type="Quantity",
                        login_details=data   
                    )
                    
                    Stock_Adjustment_History.objects.create(
                        company=com,
                        login_details=data,
                        item=item_instance,
                        date=request.data.get('adjusting_date'),
                        action='Edited',
                        stock_adjustment=stock
                    )
            elif request.data['mode_of_adjustment'] == 'Value':
                for i in stockItems:
                    item_instance = Fin_Items.objects.get(name=i.get('item'), Company=com)

                    Stock_Adjustment_Items.objects.create(
                        item=item_instance,
                        current_val = i.get('value'),
                        changed_val = i.get('changedValue'),
                        adjusted_val = i.get('difference'),
                        company=com,
                        login_details=data,
                        stock_adjustment=stock,
                        type='Value'
                    )

                    Stock_Adjustment_History.objects.create(
                        company=com,
                        login_details=data,
                        item=item_instance,
                        date=request.data.get('adjusting_date'),
                        action='Edited',
                        stock_adjustment=stock
                    )
            else:
                pass
            
            return Response(
                {"status": True, "data": serializer.data}, status=status.HTTP_200_OK
            )
        else:
            return Response(
                {"status": False, "data": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
    except Exception as e:
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


# Sales Order

@api_view(("GET",))
def Fin_fetchSalesOrderData(request, id):
    try:
        data = Fin_Login_Details.objects.get(id=id)
        if data.User_Type == "Company":
            cmp = Fin_Company_Details.objects.get(Login_Id=id)
        else:
            cmp = Fin_Staff_Details.objects.get(Login_Id=id).company_id

        items = Fin_Items.objects.filter(Company = cmp, status = 'Active')
        cust = Fin_Customers.objects.filter(Company=cmp)
        trms = Fin_Company_Payment_Terms.objects.filter(Company = cmp)
        bnk = Fin_Banking.objects.filter(company = cmp)
        lst = Fin_Price_List.objects.filter(Company = cmp, status = 'Active')
        units = Fin_Units.objects.filter(Company = cmp)
        acc = Fin_Chart_Of_Account.objects.filter(Q(account_type='Expense') | Q(account_type='Other Expense') | Q(account_type='Cost Of Goods Sold'), Company=cmp).order_by('account_name')
        custLists = Fin_Price_List.objects.filter(Company = cmp, type__iexact='sales', status = 'Active')
        
        itemSerializer = ItemSerializer(items, many=True)
        custSerializer = CustomerSerializer(cust, many=True)
        pTermSerializer = CompanyPaymentTermsSerializer(trms, many=True)
        bankSerializer = BankSerializer(bnk, many=True)
        lstSerializer = PriceListSerializer(lst, many=True)
        clSerializer = PriceListSerializer(custLists, many=True)
        unitSerializer = ItemUnitSerializer(units, many=True)
        accSerializer = AccountsSerializer(acc, many=True)

        # Fetching last sales order and assigning upcoming ref no as current + 1
        # Also check for if any bill is deleted and ref no is continuos w r t the deleted sales order
        latest_so = Fin_Sales_Order.objects.filter(Company = cmp).order_by('-id').first()

        new_number = int(latest_so.reference_no) + 1 if latest_so else 1

        if Fin_Sales_Order_Reference.objects.filter(Company = cmp).exists():
            deleted = Fin_Sales_Order_Reference.objects.get(Company = cmp)
            
            if deleted:
                while int(deleted.reference_no) >= new_number:
                    new_number+=1

        # Finding next SO number w r t last SO number if exists.
        nxtSO = ""
        lastSO = Fin_Sales_Order.objects.filter(Company = cmp).last()
        if lastSO:
            salesOrder_no = str(lastSO.sales_order_no)
            numbers = []
            stri = []
            for word in salesOrder_no:
                if word.isdigit():
                    numbers.append(word)
                else:
                    stri.append(word)
            
            num=''
            for i in numbers:
                num +=i
            
            st = ''
            for j in stri:
                st = st+j

            s_order_num = int(num)+1

            if num[0] == '0':
                if s_order_num <10:
                    nxtSO = st+'0'+ str(s_order_num)
                else:
                    nxtSO = st+ str(s_order_num)
            else:
                nxtSO = st+ str(s_order_num)

        return Response(
            {
                "status": True,
                "items": itemSerializer.data,
                "customers":custSerializer.data,
                "paymentTerms":pTermSerializer.data,
                "banks":bankSerializer.data,
                "priceList":lstSerializer.data,
                "custPriceList":clSerializer.data,
                "units":unitSerializer.data,
                "accounts":accSerializer.data,
                "refNo": new_number,
                "soNo": nxtSO,
                "state": cmp.State

            }, status=status.HTTP_200_OK
        )
    except Exception as e:
        print(e)
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

@api_view(("GET",))
def Fin_getCustomerData(request):
    try:
        custId = request.GET['c_id']
        cust = Fin_Customers.objects.get(id=custId)
        details = {
            'id':cust.id,
            'gstType': cust.gst_type,
            'email': cust.email,
            'gstIn': cust.gstin if cust.gstin else "None",
            'placeOfSupply': cust.place_of_supply,
            'address': f"{cust.billing_street},{cust.billing_city}\n{cust.billing_state}\n{cust.billing_country}\n{cust.billing_pincode}"
        }
        return Response(
            {"status": True, "customerDetails":details}, status=status.HTTP_200_OK
        )
    except Exception as e:
        print(e)
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

@api_view(("POST",))
def Fin_createNewPaymentTerm(request):
    try:
        s_id = request.data["Id"]
        data = Fin_Login_Details.objects.get(id=s_id)
        if data.User_Type == "Company":
            com = Fin_Company_Details.objects.get(Login_Id=s_id)
        else:
            com = Fin_Staff_Details.objects.get(Login_Id=s_id).company_id
        request.data["Company"] = com.id

        serializer = CompanyPaymentTermsSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"status": True, "term": serializer.data},
                status=status.HTTP_201_CREATED,
            )
        else:
            return Response(
                {"status": False, "data": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
    except Exception as e:
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

@api_view(("GET",))
def Fin_getBankAccountData(request, id):
    try:
        bank = Fin_Banking.objects.get(id=id)
        acc = bank.account_number
        return Response(
            {"status": True, "account":acc}, status=status.HTTP_200_OK
        )
    except Exception as e:
        print(e)
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

@api_view(("GET",))
def Fin_getTableItemData(request):
    try:
        s_id = request.GET["Id"]
        data = Fin_Login_Details.objects.get(id=s_id)
        if data.User_Type == "Company":
            com = Fin_Company_Details.objects.get(Login_Id=s_id)
        else:
            com = Fin_Staff_Details.objects.get(Login_Id=s_id).company_id

        itemId = request.GET['item']
        priceListId = request.GET['listId']
        item = Fin_Items.objects.get(id = itemId)

        if priceListId != "":
            priceList = Fin_Price_List.objects.get(id = int(priceListId))

            if priceList.item_rate == 'Customized individual rate':
                try:
                    priceListPrice = float(Fin_PriceList_Items.objects.get(Company = com, list = priceList, item = item).custom_rate)
                except:
                    priceListPrice = item.selling_price
            else:
                mark = priceList.up_or_down
                percentage = float(priceList.percentage)
                roundOff = priceList.round_off

                if mark == 'Markup':
                    price = float(item.selling_price) + float((item.selling_price) * (percentage/100))
                else:
                    price = float(item.selling_price) - float((item.selling_price) * (percentage/100))

                if priceList.round_off != 'Never mind':
                    if roundOff == 'Nearest whole number':
                        finalPrice = round(price)
                    else:
                        finalPrice = int(price) + float(roundOff)
                else:
                    finalPrice = price

                priceListPrice = finalPrice
        else:
            priceListPrice = None

        context = {
            'id': item.id,
            'item_type':item.item_type,
            'hsnSac':item.hsn if item.item_type == "Goods" else item.sac,
            'sales_rate':item.selling_price,
            'purchase_rate':item.purchase_price,
            'avl':item.current_stock,
            'tax': True if item.tax_reference == 'taxable' else False,
            'gst':item.intra_state_tax,
            'igst':item.inter_state_tax,
            'PLPrice':priceListPrice
        }
        return Response(
            {"status": True, "itemData":context}, status=status.HTTP_200_OK
        )
    except Exception as e:
        print(e)
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

@api_view(("GET",))
def Fin_checkSalesOrderNo(request):
    try:
        s_id = request.GET["Id"]
        data = Fin_Login_Details.objects.get(id=s_id)
        if data.User_Type == "Company":
            com = Fin_Company_Details.objects.get(Login_Id=s_id)
        else:
            com = Fin_Staff_Details.objects.get(Login_Id=s_id).company_id

        SONo = request.GET['SONum']

        nxtSO = ""
        lastSOrder = Fin_Sales_Order.objects.filter(Company = com).last()
        if lastSOrder:
            salesOrder_no = str(lastSOrder.sales_order_no)
            numbers = []
            stri = []
            for word in salesOrder_no:
                if word.isdigit():
                    numbers.append(word)
                else:
                    stri.append(word)
            
            num=''
            for i in numbers:
                num +=i
            
            st = ''
            for j in stri:
                st = st+j

            s_order_num = int(num)+1

            if num[0] == '0':
                if s_order_num <10:
                    nxtSO = st+'0'+ str(s_order_num)
                else:
                    nxtSO = st+ str(s_order_num)
            else:
                nxtSO = st+ str(s_order_num)

        if Fin_Sales_Order.objects.filter(Company = com, sales_order_no__iexact = SONo).exists():
            return Response({'status':False, 'message':'Sales Order No. already Exists.!'})
        elif nxtSO != "" and SONo != nxtSO:
            return Response({'status':False, 'message':'Sales Order No. is not continuous.!'})
        else:
            return Response({'status':True, 'message':'Number is okay.!'})
    except Exception as e:
        print(e)
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

@api_view(("POST",))
@parser_classes((MultiPartParser, FormParser))
def Fin_createSalesOrder(request):
    try:
        s_id = request.data["Id"]
        data = Fin_Login_Details.objects.get(id=s_id)
        if data.User_Type == "Company":
            com = Fin_Company_Details.objects.get(Login_Id=s_id)
        else:
            com = Fin_Staff_Details.objects.get(Login_Id=s_id).company_id

        # Make a mutable copy of request.data
        mutable_data = deepcopy(request.data)
        mutable_data["Company"] = com.id
        mutable_data["LoginDetails"] = com.Login_Id.id
        mutable_data["exp_ship_date"] = datetime.strptime(request.data['exp_ship_date'], '%d-%m-%Y').date()
        mutable_data["price_list"] = None if request.data["price_list"] == 'null' else request.data["price_list"]

        # Parse stock_items from JSON
        salesItems = json.loads(request.data['salesOrderItems'])
        SONum = request.data['sales_order_no']
        if Fin_Sales_Order.objects.filter(Company = com, sales_order_no__iexact = SONum).exists():
            return Response({'status':False, 'message': f"Sales Order Number '{SONum}' already exists, try another!"})
        else:
            serializer = SalesOrderSerializer(data=mutable_data, partial=True)
            if serializer.is_valid():
                serializer.save()
                sale = Fin_Sales_Order.objects.get(id=serializer.data['id'])

                for ele in salesItems:
                    itm = Fin_Items.objects.get(id = int(ele.get('item')))
                    hsn = ele.get('hsnSac') if itm.item_type == 'Goods' else None
                    sac = ele.get('hsnSac') if itm.item_type != 'Goods' else None
                    price = ele.get('priceListPrice') if sale.price_list_applied else ele.get('price')
                    tax = ele.get('taxGst') if com.State == request.data['place_of_supply'] else ele.get('taxIgst')
                    disc = float(ele.get('discount')) if ele.get('discount') != "" else 0.0
                    Fin_Sales_Order_Items.objects.create(SalesOrder = sale, Item = itm, hsn = hsn,sac=sac, quantity = int(ele.get('quantity')), price = float(price), tax = tax, discount = disc, total = float(ele.get('total')))
            
                # Save transaction
                        
                Fin_Sales_Order_History.objects.create(
                    Company = com,
                    LoginDetails = data,
                    SalesOrder = sale,
                    action = 'Created'
                )
                
                return Response(
                    {"status": True, "data": serializer.data}, status=status.HTTP_200_OK
                )
            else:
                return Response(
                    {"status": False, "data": serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST,
                )
    except Exception as e:
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

@api_view(("GET",))
def Fin_fetchSalesOrders(request, id):
    try:
        data = Fin_Login_Details.objects.get(id=id)
        if data.User_Type == "Company":
            com = Fin_Company_Details.objects.get(Login_Id=id)
        else:
            com = Fin_Staff_Details.objects.get(Login_Id=id).company_id

        sales = Fin_Sales_Order.objects.filter(Company = com)
        sls = []
        for i in sales:
            obj = {
                "id": i.id,
                "sales_order_no": i.sales_order_no,
                "customer_name": i.Customer.first_name+" "+i.Customer.last_name,
                "customer_email":i. customer_email,
                "grandtotal": i.grandtotal,
                "status": i.status,
                "balance": i.balance,
            }
            sls.append(obj)
        return Response(
            {"status": True, "salesOrder": sls}, status=status.HTTP_200_OK
        )
    except Exception as e:
        print(e)
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

@api_view(("GET",))
def Fin_fetchSalesOrderDetails(request, id):
    try:
        sales = Fin_Sales_Order.objects.get(id=id)
        cmp = sales.Company
        hist = Fin_Sales_Order_History.objects.filter(SalesOrder=sales).last()
        his = None
        if hist:
            his = {
                "action": hist.action,
                "date": hist.date,
                "doneBy": hist.LoginDetails.First_name
                + " "
                + hist.LoginDetails.Last_name,
            }
        cmt = Fin_Sales_Order_Comments.objects.filter(SalesOrder=sales)
        itms = Fin_Sales_Order_Items.objects.filter(SalesOrder=sales)
        try:
            created = Fin_Sales_Order_History.objects.get(SalesOrder = sales, action = 'Created')
        except:
            created = None
        otherDet = {
            "Company_name": cmp.Company_name,
            "Email": cmp.Email,
            "Mobile": cmp.Contact,
            "Address": cmp.Address,
            "City": cmp.City,
            "State": cmp.State,
            "Pincode": cmp.Pincode,
            "customerName": sales.Customer.first_name+' '+sales.Customer.last_name,
            "customerEmail": sales.Customer.email,
            "createdBy": created.LoginDetails.First_name if created else ""
        }
        items = []
        for i in itms:
            obj = {
                "id":i.id,
                "itemId": i.Item.id,
                "sales_price": i.Item.selling_price,
                'name': i.Item.name,
                "item_type": i.Item.item_type,
                "hsn": i.hsn,
                "sac": i.sac,
                "quantity": i.quantity,
                "price": i.price,
                "tax": i.tax,
                "discount": i.discount,
                "total": i.total
            }
            items.append(obj)
        salesSerializer = SalesOrderSerializer(sales)
        commentsSerializer = SalesOrderCommentSerializer(cmt, many=True)
        return Response(
            {
                "status": True,
                "sales": salesSerializer.data,
                "history": his,
                "comments": commentsSerializer.data,
                "items": items,
                "otherDetails": otherDet,
            },
            status=status.HTTP_200_OK,
        )
    except Exception as e:
        print(e)
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

@api_view(("POST",))
def Fin_changeSalesOrderStatus(request):
    try:
        salesId = request.data["id"]
        data = Fin_Sales_Order.objects.get(id=salesId)
        data.status = "Saved"
        data.save()
        return Response({"status": True}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

@api_view(("POST",))
def Fin_addSalesOrderComment(request):
    try:
        id = request.data["Id"]
        data = Fin_Login_Details.objects.get(id=id)
        if data.User_Type == "Company":
            com = Fin_Company_Details.objects.get(Login_Id=id)
        else:
            com = Fin_Staff_Details.objects.get(Login_Id=id).company_id

        request.data["Company"] = com.id
        serializer = SalesOrderCommentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"status": True, "data": serializer.data}, status=status.HTTP_200_OK
            )
        else:
            return Response(
                {"status": False, "data": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
    except Exception as e:
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

@api_view(("DELETE",))
def Fin_deleteSalesOrderComment(request, id):
    try:
        cmt = Fin_Sales_Order_Comments.objects.get(id=id)
        cmt.delete()
        return Response({"status": True}, status=status.HTTP_200_OK)
    except Exception as e:
        print(e)
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

@api_view(("GET",))
def Fin_fetchSalesOrderHistory(request, id):
    try:
        sales = Fin_Sales_Order.objects.get(id=id)
        hist = Fin_Sales_Order_History.objects.filter(SalesOrder=sales)
        his = []
        if hist:
            for i in hist:
                h = {
                    "action": i.action,
                    "date": i.date,
                    "name": i.LoginDetails.First_name + " " + i.LoginDetails.Last_name,
                }
                his.append(h)
        salesSerializer = SalesOrderSerializer(sales)
        return Response(
            {"status": True, "salesOrder": salesSerializer.data, "history": his},
            status=status.HTTP_200_OK,
        )
    except Exception as e:
        print(e)
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

@api_view(("POST",))
@parser_classes((MultiPartParser, FormParser))
def Fin_addSalesOrderAttachment(request):
    try:
        s_id = request.data["Id"]
        data = Fin_Login_Details.objects.get(id=s_id)
        if data.User_Type == "Company":
            com = Fin_Company_Details.objects.get(Login_Id=s_id)
        else:
            com = Fin_Staff_Details.objects.get(Login_Id=s_id).company_id

        sId = request.data['sales_id']
        sale = Fin_Sales_Order.objects.get(id=sId)
        if request.data['file']:
            sale.file = request.data['file']
        sale.save()
        return Response(
            {"status": True}, status=status.HTTP_200_OK
        )
    except Exception as e:
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

@api_view(("DELETE",))
def Fin_deleteSalesOrder(request, id):
    try:
        sales = Fin_Sales_Order.objects.get(id=id)
        com = sales.Company
        Fin_Sales_Order_Items.objects.filter(SalesOrder = sales).delete()

        # Storing ref number to deleted table
        # if entry exists and lesser than the current, update and save => Only one entry per company
        if Fin_Sales_Order_Reference.objects.filter(Company = com).exists():
            deleted = Fin_Sales_Order_Reference.objects.get(Company = com)
            if int(sales.reference_no) > int(deleted.reference_no):
                deleted.reference_no = sales.reference_no
                deleted.save()
        else:
            Fin_Sales_Order_Reference.objects.create(Company = com, reference_no = sales.reference_no)
        sales.delete()
        return Response({"status": True}, status=status.HTTP_200_OK)
    except Exception as e:
        print(e)
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

@api_view(("GET",))
def Fin_salesOrderPdf(request):
    try:
        id = request.GET['Id']
        slId = request.GET['sales_id']

        data = Fin_Login_Details.objects.get(id=id)
        if data.User_Type == "Company":
            com = Fin_Company_Details.objects.get(Login_Id=data.id)
        else:
            com = Fin_Staff_Details.objects.get(Login_Id=data.id).company_id

        salesOrder = Fin_Sales_Order.objects.get(id=slId)
        itms = Fin_Sales_Order_Items.objects.filter(SalesOrder=salesOrder)
        context = {'order':salesOrder, 'orderItems':itms,'cmp':com}
        
        template_path = 'company/Fin_Sales_Order_Pdf.html'
        fname = 'Sales_Order_'+salesOrder.sales_order_no
        # Create a Django response object, and specify content_type as pdftemp_
        response = HttpResponse(content_type="application/pdf")
        response["Content-Disposition"] = f"attachment; filename = {fname}.pdf"
        # find the template and render it.
        template = get_template(template_path)
        html = template.render(context)

        # create a pdf
        pisa_status = pisa.CreatePDF(html, dest=response)
        # if error then show some funny view
        if pisa_status.err:
            return HttpResponse("We had some errors <pre>" + html + "</pre>")
        return response
    except Exception as e:
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

@api_view(("POST",))
def Fin_shareSalesOrderToEmail(request):
    try:
        id = request.data["Id"]
        data = Fin_Login_Details.objects.get(id=id)
        if data.User_Type == "Company":
            com = Fin_Company_Details.objects.get(Login_Id=data.id)
        else:
            com = Fin_Staff_Details.objects.get(Login_Id=data.id).company_id

        slId = request.data["sales_id"]

        emails_string = request.data["email_ids"]

        # Split the string by commas and remove any leading or trailing whitespace
        emails_list = [email.strip() for email in emails_string.split(",")]
        email_message = request.data["email_message"]
        # print(emails_list)

        salesOrder = Fin_Sales_Order.objects.get(id=slId)
        itms = Fin_Sales_Order_Items.objects.filter(SalesOrder=salesOrder)
        context = {'order':salesOrder, 'orderItems':itms,'cmp':com}
        
        template_path = 'company/Fin_Sales_Order_Pdf.html'
        template = get_template(template_path)

        html = template.render(context)
        result = BytesIO()
        pdf = pisa.pisaDocument(BytesIO(html.encode("ISO-8859-1")), result)
        pdf = result.getvalue()
        filename = f'SalesOrder_{salesOrder.sales_order_no}.pdf'
        subject = f"SalesOrder_{salesOrder.sales_order_no}"
        email = EmailMessage(
            subject,
            f"Hi,\nPlease find the attached details - SALES ORDER-{salesOrder.sales_order_no}. \n{email_message}\n\n--\nRegards,\n{com.Company_name}\n{com.Address}\n{com.State} - {com.Country}\n{com.Contact}",
            from_email=settings.EMAIL_HOST_USER,
            to=emails_list,
        )
        email.attach(filename, pdf, "application/pdf")
        email.send(fail_silently=False)

        return Response({"status": True}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

@api_view(("PUT",))
@parser_classes((MultiPartParser, FormParser))
def Fin_updateSalesOrder(request):
    try:
        s_id = request.data["Id"]
        data = Fin_Login_Details.objects.get(id=s_id)
        if data.User_Type == "Company":
            com = Fin_Company_Details.objects.get(Login_Id=s_id)
        else:
            com = Fin_Staff_Details.objects.get(Login_Id=s_id).company_id

        sales = Fin_Sales_Order.objects.get(id=request.data['sales_id'])
        # Make a mutable copy of request.data

        mutable_data = deepcopy(request.data)
        mutable_data["Company"] = com.id
        mutable_data["LoginDetails"] = com.Login_Id.id
        mutable_data["exp_ship_date"] = datetime.strptime(request.data['exp_ship_date'], '%Y-%m-%d').date()
        mutable_data["price_list"] = None if request.data["price_list"] == 'null' else request.data["price_list"]

        # Parse stock_items from JSON
        salesItems = json.loads(request.data['salesOrderItems'])
        SONum = request.data['sales_order_no']
        if sales.sales_order_no != SONum and Fin_Sales_Order.objects.filter(Company = com, sales_order_no__iexact = SONum).exists():
            return Response({'status':False, 'message': f"Sales Order Number '{SONum}' already exists, try another!"})
        else:
            serializer = SalesOrderSerializer(sales,data=mutable_data, partial=True)
            if serializer.is_valid():
                serializer.save()
                Fin_Sales_Order_Items.objects.filter(SalesOrder = sales).delete()
                sale = Fin_Sales_Order.objects.get(id=serializer.data['id'])

                for ele in salesItems:
                    itm = Fin_Items.objects.get(id = int(ele.get('item')))
                    hsn = ele.get('hsnSac') if itm.item_type == 'Goods' else None
                    sac = ele.get('hsnSac') if itm.item_type != 'Goods' else None
                    price = ele.get('priceListPrice') if sale.price_list_applied else ele.get('price')
                    tax = ele.get('taxGst') if com.State == request.data['place_of_supply'] else ele.get('taxIgst')
                    disc = float(ele.get('discount')) if ele.get('discount') != "" else 0.0
                    Fin_Sales_Order_Items.objects.create(SalesOrder = sale, Item = itm, hsn = hsn,sac=sac, quantity = int(ele.get('quantity')), price = float(price), tax = tax, discount = disc, total = float(ele.get('total')))
            
                # Save transaction
                        
                Fin_Sales_Order_History.objects.create(
                    Company = com,
                    LoginDetails = data,
                    SalesOrder = sales,
                    action = 'Edited'
                )
                
                return Response(
                    {"status": True, "data": serializer.data}, status=status.HTTP_200_OK
                )
            else:
                return Response(
                    {"status": False, "data": serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST,
                )
    except Exception as e:
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
        
#End
# Vendor
@api_view(("POST",))
def Fin_add_vendor_new(request):
    try:
        v_id = request.data["Id"]
        data = Fin_Login_Details.objects.get(id=v_id)
        if data.User_Type == "Company":
            com = Fin_Company_Details.objects.get(Login_Id=v_id)
        else:
            com = Fin_Staff_Details.objects.get(Login_Id=v_id).company_id
        title = request.data["Title"]
        fname = request.data["Firstname"]
        lname = request.data["Lastname"]
        company = request.data["Company"]
        location = request.data["Location"]
        email = request.data["Email"]
        website = request.data["Website"]
        mobile = request.data["Mobile"]
        gsttype = request.data["Gsttype"]
        gstno = request.data["Gstno"]
        pan = request.data["Panno"]
        placeofsupply = request.data["Placeofsupply"]
        currency = request.data["Currency"]
        openingbal = request.data["Openingbalance"]
        openingbaltype = request.data["Openingbalatype"]
        creditlimit = request.data["Creditlimit"]
        paymentterm = request.data["Payment"]
        bilstr = request.data["Billingstreet"]
        bilcountry = request.data["Billingcountry"]
        bilstate = request.data["Billingstate"]
        bilpin = request.data["Billingpin"]
        bilcity = request.data["Billingcity"]
        shipstr = request.data["Shipstreet"]
        shipcountry = request.data["Shipcountry"]
        shipstate = request.data["Shipstate"]
        shipcity = request.data["Shipcity"]
        shippin = request.data["Shippin"]
        st = request.data["status"]
        term = Fin_Company_Payment_Terms.objects.get(id=paymentterm)
        vendor = Fin_Vendor.objects.create(Title=title,First_name=fname,Last_name=lname,Vendor_email=email,Mobile=mobile,Company_Name=company,Location=location,Website=website,
                                           GST_Treatment=gsttype,GST_Number=gstno,Pan_Number=pan,Opening_balance_type=openingbaltype,Opening_balance=openingbal,Credit_limit=creditlimit,
                                           Place_of_supply=placeofsupply,Billing_street=bilstr,Billing_city=bilcity,Billing_state=bilstate,Billing_country=bilcountry,Billing_pincode=bilpin,
                                           Shipping_street=shipstr,Shipping_city=shipcity,Shipping_state=shipstate,Shipping_country=shipcountry,Shipping_pincode=shippin,status=st,Company=com,Login_details=data,currency=currency,payment_terms=term)
        vendor.save()
        history = Fin_Vendor_History.objects.create(Company=com,Login_details=data,Vendor=vendor,Action='Created')
        history.save()
        return Response({"status": True, "message": 'Success'})
    except Exception as e:
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
    
@api_view(("GET",))
def Fin_all_vendors(request,id):
    try:
        data = Fin_Login_Details.objects.get(id=id)
        if data.User_Type == "Company":
            com = Fin_Company_Details.objects.get(Login_Id=id)
        else:
            com = Fin_Staff_Details.objects.get(Login_Id=id).company_id
        vendors = Fin_Vendor.objects.filter(Company=com)
        serializer = VendorSerializer(vendors, many=True)
        return Response(
            {"status": True, "vendors": serializer.data}, status=status.HTTP_200_OK
        )
    except Exception as e:
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
    
@api_view(("GET",))
# @api_view(['POST'])
def Fin_view_vendor(request,id,ID):
    try:
        data = Fin_Login_Details.objects.get(id=ID)
        if data.User_Type == "Company":
            com = Fin_Company_Details.objects.get(Login_Id=ID)
        else:
            com = Fin_Staff_Details.objects.get(Login_Id=ID).company_id
        vendor = Fin_Vendor.objects.get(id=id)
        serializer = VendorSerializer(vendor)
        company = CompanyDetailsSerializer(com)
        pt = vendor.payment_terms
        payment_term = pt.term_name
        his = Fin_Vendor_History.objects.filter(Vendor=vendor).last()
        cmt = Fin_Vendor_Comments.objects.filter(Vendor=vendor)
        commentsSerializer = VendorCommentSerializer(cmt, many=True)
        if his:
           hist = {
                    "action": his.Action,
                "date": his.Date,
                "doneBy": his.Login_details.First_name
                + " "
                + his.Login_details.Last_name,
            }
           
        return Response({"status":True,"vendors":serializer.data,"company":company.data,"payment_term":payment_term,"history":hist,"comments":commentsSerializer.data}, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
    
@api_view(("POST",))
def Fin_change_vendor_status(request,id,sta):
    try:
        vendor = Fin_Vendor.objects.get(id=id)
        if vendor.status == 'Active':
            vendor.status = sta
            vendor.save()
            return Response({"status":True,"message":"Changed"}, status=status.HTTP_200_OK)
        elif vendor.status == 'Inactive':
            vendor.status = sta
            vendor.save()
            return Response({"status":True,"message":"Changed"}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

@api_view(("GET",))
def Fin_vendorTransactionsPdf(request, ID, id):
    try:
        data = Fin_Login_Details.objects.get(id=ID)
        if data.User_Type == "Company":
            com = Fin_Company_Details.objects.get(Login_Id=ID)
        else:
            com = Fin_Staff_Details.objects.get(Login_Id=ID).company_id

        vnd = Fin_Vendor.objects.get(id = id)

        Bal = 0
        combined_data=[]
        dict = {
            'Type' : 'Opening Balance', 'Number' : "", 'Total': vnd.Opening_balance, 'Balance': vnd.Opening_balance
        }
        combined_data.append(dict)
# , 'Date' : vnd.date
        if vnd.Opening_balance_type == 'credit':
            Bal += float(vnd.Opening_balance)
        else:
            Bal -= float(vnd.Opening_balance)
        context = {'vendor':vnd, 'cmp':com, 'BALANCE':Bal, 'combined_data':combined_data}
        template_path = 'company/Fin_Vendor_Transaction_Pdf.html'
        fname = 'Vendor_Transactions_'+vnd.First_name+'_'+vnd.Last_name
        # return render(request, 'company/Fin_Vendor_Transaction_Pdf.html',context)
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] =f'attachment; filename = {fname}.pdf'
        template = get_template(template_path)
        html = template.render(context)
        pisa_status = pisa.CreatePDF(
        html, dest=response)
        if pisa_status.err:
            return HttpResponse("We had some errors <pre>" + html + "</pre>")
        return response
    except Exception as e:
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

@api_view(("POST",))
def Fin_sharevendorTransactionsToEmail(request):
    try:
        id = request.data["Id"]
        data = Fin_Login_Details.objects.get(id=id)
        if data.User_Type == "Company":
            com = Fin_Company_Details.objects.get(Login_Id=id)
        else:
            com = Fin_Staff_Details.objects.get(Login_Id=id).company_id

        vedorid = request.data["id"]
        vendor = Fin_Vendor.objects.get(id=vedorid)
        emails_string = request.data["email_ids"]

        # Split the string by commas and remove any leading or trailing whitespace
        emails_list = [email.strip() for email in emails_string.split(",")]
        email_message = request.data["email_message"]
        # print(emails_list)'Date' : vnd.date,

        Bal = 0
        combined_data=[]
        dict = {
            'Type' : 'Opening Balance', 'Number' : "",  'Total': vendor.Opening_balance, 'Balance': vendor.Opening_balance
        }
        combined_data.append(dict)
        if vendor.Opening_balance_type == 'credit':
            Bal += float(vendor.Opening_balance)
        else:
            Bal -= float(vendor.Opening_balance)
    
        context = {'vendor':vendor, 'cmp':com, 'BALANCE':Bal, 'combined_data':combined_data}
        template_path = "company/Fin_Vendor_Transaction_Pdf.html"
        template = get_template(template_path)

        html = template.render(context)
        result = BytesIO()
        pdf = pisa.pisaDocument(BytesIO(html.encode("ISO-8859-1")), result)
        pdf = result.getvalue()
        filename = f'Vendor_Transactions_{vendor.First_name}_{vendor.Last_name}'
        subject = f"Vendor_Transactions_{vendor.First_name}_{vendor.Last_name}"
        email = EmailMessage(
            subject,
            f"Hi,\nPlease find the attached Transaction details for - Vendor-{vendor.First_name} {vendor.Last_name}. \n{email_message}\n\n--\nRegards,\n{com.Company_name}\n{com.Address}\n{com.State} - {com.Country}\n{com.Contact}",
            from_email=settings.EMAIL_HOST_USER,
            to=emails_list,
        )
        email.attach(filename, pdf, "application/pdf")
        email.send(fail_silently=False)

        return Response({"status": True}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
    
@api_view(("GET",))
def Fin_get_vendor_details(request,id,ID):
    try:
        log = Fin_Login_Details.objects.get(id=ID)
        login = LoginDetailsSerializer(log)
        vend = Fin_Vendor.objects.get(id=id)
        vendor = VendorSerializer(vend)
        if log.User_Type == "Company":
            com = Fin_Company_Details.objects.get(Login_Id = ID)
            company = CompanyDetailsSerializer(com)
            trms = Fin_Company_Payment_Terms.objects.filter(Company = com)
            ctrms = CompanyPaymentTermsSerializer(trms)
            return Response({"status": True,'com':company.data,'data':login.data,'vendor':vendor.data,'pTerms':ctrms.data}, status=status.HTTP_200_OK)
        else:
            com = Fin_Staff_Details.objects.get(Login_Id = ID)
            company = CompanyDetailsSerializer(com)
            trms = Fin_Company_Payment_Terms.objects.filter(Company = com.company_id)
            ctrms = CompanyPaymentTermsSerializer(trms)
            return Response({"status": True,'com':company.data,'data':login.data,'vendor':vendor.data,'pTerms':ctrms.data}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

@api_view(("PUT",))
def Fin_update_vendor(request):
    try:
        v_id = request.data["Id"]
        data = Fin_Login_Details.objects.get(id=v_id)
        if data.User_Type == "Company":
            com = Fin_Company_Details.objects.get(Login_Id=v_id)
        else:
            com = Fin_Staff_Details.objects.get(Login_Id=v_id).company_id
        vendid = request.data["id"]
        vendor = Fin_Vendor.objects.get(id=vendid)
        vendor.Title = request.data["Title"]
        vendor.First_name = request.data["Firstname"]
        vendor.Last_name = request.data["Lastname"]
        vendor.Company_Name = request.data["Company"]
        vendor.Location = request.data["Location"]
        vendor.Vendor_email = request.data["Email"]
        vendor.Website = request.data["Website"]
        vendor.Mobile = request.data["Mobile"]
        vendor.GST_Treatment = request.data["Gsttype"]
        vendor.GST_Number = request.data["Gstno"]
        vendor.Pan_Number = request.data["Panno"]
        vendor.Place_of_supply = request.data["Placeofsupply"]
        vendor.Opening_balance = request.data["Openingbalance"]
        vendor.Opening_balance_type = request.data["Openingbalatype"]
        vendor.Credit_limit = request.data["Creditlimit"]
        vendor.Billing_street = request.data["Billingstreet"]
        vendor.Billing_city = request.data["Billingcity"]
        vendor.Billing_country = request.data["Billingcountry"]
        vendor.Billing_pincode = request.data["Billingpin"]
        vendor.Billing_state = request.data["Billingstate"]
        vendor.Shipping_city = request.data["Shipcity"]
        vendor.Shipping_country = request.data["Shipcountry"]
        vendor.Shipping_pincode = request.data["Shippin"]
        vendor.Shipping_state = request.data["Shipstate"]
        vendor.Shipping_street = request.data["Shipstreet"]
        payment_terms = request.data["Payment"]
        term = Fin_Company_Payment_Terms.objects.get(id=payment_terms)
        vendor.payment_terms = term
        vendor.save()
        history = Fin_Vendor_History.objects.create(Company=com,Login_details=data,Vendor=vendor,Action='Edited')
        history.save()
        return Response({"status": True}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

@api_view(("DELETE",))
def Fin_delete_vendor(request,id):
    try:
        vendor = Fin_Vendor.objects.get(id=id)
        vendor.delete()
        return Response({"status": True}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )    
    
@api_view(("POST",))
def Fin_add_vendor_comment(request):
    try:
        c_id = request.data["Id"]
        data = Fin_Login_Details.objects.get(id=c_id)
        if data.User_Type == "Company":
            com = Fin_Company_Details.objects.get(Login_Id=c_id)
        else:
            com = Fin_Staff_Details.objects.get(Login_Id=c_id).company_id
        vendor_id = request.data["id"]
        vendor = Fin_Vendor.objects.get(id=vendor_id)
        comments = request.data["comments"]
        comm = Fin_Vendor_Comments.objects.create(Company=com,Vendor=vendor,comments=comments)
        serializer = VendorCommentSerializer(comm)
        comm.save()
        return Response({"status": True,"comments":serializer.data}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
    
@api_view(("DELETE",))
def Fin_delete_vendor_comment(request,id):
    try:
        comment = Fin_Vendor_Comments.objects.get(id=id)
        comment.delete()
        return Response({"status": True}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        ) 
    
@api_view(("GET",))
def Fin_fetch_vendor_history(request, id):
    try:
        vendor = Fin_Vendor.objects.get(id=id)
        hist = Fin_Vendor_History.objects.filter(Vendor=vendor)
        his = []
        if hist:
            for i in hist:
                h = {
                    "action": i.Action,
                    "date": i.Date,
                    "name": i.Login_details.First_name + " " + i.Login_details.Last_name,
                }
                his.append(h)
        vendorserializer = VendorSerializer(vendor)
        return Response(
            {"status": True, "vendor": vendorserializer.data, "history": his},
            status=status.HTTP_200_OK,
        )
    except Exception as e:
        print(e)
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
        
#End

#Purchase Order

@api_view(("GET",))
def Fin_fetch_vendors(request,ID):
    try:
        data = Fin_Login_Details.objects.get(id=ID)
        if data.User_Type == "Company":
            com = Fin_Company_Details.objects.get(Login_Id=ID)
        else:
            com = Fin_Staff_Details.objects.get(Login_Id=ID).company_id
        vendors = Fin_Vendor.objects.filter(Company=com)
        serializer = VendorSerializer(vendors, many=True)
        return Response(
            {"status": True, "vendors": serializer.data}, status=status.HTTP_200_OK
        )
    except Exception as e:
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
    
@api_view(("GET",))
def Fin_get_vendor_details(request,id):
    try:
        vend = Fin_Vendor.objects.get(id=id)
        details = {
            'id':vend.id,
            'gstType': vend.GST_Treatment,
            'email': vend.Vendor_email,
            'gstIn': vend.GST_Number if vend.GST_Number else "None",
            'placeOfSupply': vend.Place_of_supply,
            'address': f"{vend.Billing_street},{vend.Billing_city}\n{vend.Billing_state}\n{vend.Billing_country}\n{vend.Billing_pincode}",
            'name': f"{vend.Title}. {vend.First_name} {vend.Last_name}"
        }
        return Response(
            {"status": True, "vendorDetails":details}, status=status.HTTP_200_OK
        )
    except Exception as e:
        print(e)
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
    
@api_view(("GET",))
def Fin_fetch_customers(request,ID):
    try:
        data = Fin_Login_Details.objects.get(id=ID)
        if data.User_Type == "Company":
            com = Fin_Company_Details.objects.get(Login_Id=ID)
        else:
            com = Fin_Staff_Details.objects.get(Login_Id=ID).company_id
        customers = Fin_Customers.objects.filter(Company=com)
        serializer = CustomerSerializer(customers, many=True)
        return Response(
            {"status": True, "customers": serializer.data}, status=status.HTTP_200_OK
        )
    except Exception as e:
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
    
@api_view(("GET",))
def Fin_get_customer_details(request,id):
    try:
        cust = Fin_Customers.objects.get(id=id)
        details = {
            'id':cust.id,
            'gstType': cust.gst_type,
            'email': cust.email,
            'gstIn': cust.gstin if cust.gstin else "None",
            'placeOfSupply': cust.place_of_supply,
            'address': f"{cust.billing_street},{cust.billing_city}\n{cust.billing_state}\n{cust.billing_country}\n{cust.billing_pincode}",
            'name': f"{cust.title}. {cust.first_name} {cust.last_name}"
        }
        return Response(
            {"status": True, "customerDetails":details}, status=status.HTTP_200_OK
        )
    except Exception as e:
        print(e)
        return Response(
            {"status": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
    