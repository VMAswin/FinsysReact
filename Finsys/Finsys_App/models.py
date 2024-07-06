#React Finsys

from django.db import models
from django.utils import timezone
from datetime import date
# Create your models here.

class Fin_Payment_Terms(models.Model):
    payment_terms_number = models.IntegerField(null=True,blank=True)  
    payment_terms_value = models.CharField(max_length=100,null=True,blank=True) 
    days = models.CharField(max_length=100,null=True,blank=True) 

class Fin_Login_Details(models.Model):
    First_name = models.CharField(max_length=255,null=True,blank=True)
    Last_name = models.CharField(max_length=255,null=True,blank=True)
    User_name = models.CharField(max_length=255,null=True,blank=True)
    password = models.CharField(max_length=100,null=True,blank=True)
    User_Type = models.CharField(max_length=255,null=True,blank=True) 

class Fin_Distributors_Details(models.Model):  
    Login_Id = models.ForeignKey(Fin_Login_Details, on_delete=models.CASCADE,null=True,blank=True)
    Payment_Term =  models.ForeignKey(Fin_Payment_Terms, on_delete=models.CASCADE,null=True,blank=True)
    Distributor_Code = models.CharField(max_length=100,null=True,blank=True)
    Email = models.CharField(max_length=255,null=True,blank=True) 
    Contact = models.CharField(max_length=255,null=True,blank=True)
    Image = models.ImageField(null=True,blank = True,upload_to = 'image/distributor') 
    Start_Date = models.DateField(auto_now_add=True,null=True)
    End_date = models.DateField(max_length=255,null=True,blank=True)
    Admin_approval_status = models.CharField(max_length=255,null=True,blank=True)   

class Fin_Company_Details(models.Model): 
    Payment_Term = models.ForeignKey(Fin_Payment_Terms, on_delete=models.CASCADE,null=True,blank=True)
    Distributor_id = models.ForeignKey(Fin_Distributors_Details, on_delete=models.CASCADE,null=True,blank=True)
    Login_Id = models.ForeignKey(Fin_Login_Details, on_delete=models.CASCADE,null=True,blank=True)
    Company_name = models.CharField(max_length=255,null=True,blank=True)
    Business_name = models.CharField(max_length=255,null=True,blank=True)
    Industry = models.CharField(max_length=255,null=True,blank=True)
    Company_Type = models.CharField(max_length=255,null=True,blank=True)

    Company_Code = models.CharField(max_length=100,null=True,blank=True)
    Email = models.CharField(max_length=255,null=True,blank=True) 
    Contact = models.CharField(max_length=255,null=True,blank=True)
    Address = models.TextField(max_length=255,null=True,blank=True)
    City = models.CharField(max_length=255,null=True,blank=True)
    State = models.CharField(max_length=255,null=True,blank=True)
    Country = models.CharField(max_length=255,null=True,blank=True)
    Pincode = models.IntegerField(null=True,blank=True)
    Pan_NO = models.CharField(max_length=255,null=True,blank=True)
    GST_Type = models.CharField(max_length=255,null=True,blank=True)
    GST_NO = models.CharField(max_length=255,null=True,blank=True)
    Image = models.ImageField(null=True,blank = True,upload_to = 'image/company') 
    Start_Date = models.DateField(auto_now_add=True,null=True)
    End_date = models.DateField(max_length=255,null=True,blank=True)
    Payment_Type = models.CharField(max_length=255,null=True,blank=True)
    Accountant = models.CharField(max_length=255,null=True,blank=True)
    Admin_approval_status = models.CharField(max_length=255,null=True,blank=True)
    Distributor_approval_status = models.CharField(max_length=255,null=True,blank=True)
    Registration_Type = models.CharField(max_length=255,null=True,blank=True)

class Fin_Modules_List(models.Model):
    Login_Id = models.ForeignKey(Fin_Login_Details, on_delete=models.CASCADE,null=True,blank=True)
    company_id = models.ForeignKey(Fin_Company_Details, on_delete=models.CASCADE,null=True,blank=True)

    # -----items-----
    Items = models.IntegerField(null=True,default=0) 
    Price_List = models.IntegerField(null=True,default=0) 
    Stock_Adjustment = models.IntegerField(null=True,default=0) 

    # --------- CASH & BANK-----
    Cash_in_hand = models.IntegerField(null=True,default=0) 
    Offline_Banking = models.IntegerField(null=True,default=0)
    Bank_Reconciliation = models.IntegerField(null=True,default=0)
    UPI = models.IntegerField(null=True,default=0)
    Bank_Holders = models.IntegerField(null=True,default=0)
    Cheque = models.IntegerField(null=True,default=0)
    Loan_Account = models.IntegerField(null=True,default=0)

    #  ------SALES MODULE -------
    Customers  = models.IntegerField(null=True,default=0)
    Invoice = models.IntegerField(null=True,default=0) 
    Estimate = models.IntegerField(null=True,default=0) 
    Sales_Order = models.IntegerField(null=True,default=0) 
    Recurring_Invoice = models.IntegerField(null=True,default=0) 
    Retainer_Invoice = models.IntegerField(null=True,default=0) 
    Credit_Note = models.IntegerField(null=True,default=0) 
    Payment_Received = models.IntegerField(null=True,default=0) 
    Delivery_Challan = models.IntegerField(null=True,default=0)

    #  ---------PURCHASE MODULE--------- 
    Vendors = models.IntegerField(null=True,default=0) 
    Bills = models.IntegerField(null=True,default=0) 
    Recurring_Bills = models.IntegerField(null=True,default=0) 
    Debit_Note = models.IntegerField(null=True,default=0) 
    Purchase_Order = models.IntegerField(null=True,default=0) 
    Expenses = models.IntegerField(null=True,default=0) 
    Recurring_Expenses = models.IntegerField(null=True,default=0) 
    Payment_Made = models.IntegerField(null=True,default=0) 

    # --------EWay_Bill-----
    EWay_Bill = models.IntegerField(null=True,default=0) 

    #  -------ACCOUNTS--------- 
    Chart_of_Accounts = models.IntegerField(null=True,default=0)  
    Manual_Journal = models.IntegerField(null=True,default=0)  
    Reconcile = models.IntegerField(null=True,default=0) 

    # -------PAYROLL------- 
    Employees = models.IntegerField(null=True,default=0) 
    Employees_Loan = models.IntegerField(null=True,default=0)  
    Holiday = models.IntegerField(null=True,default=0) 
    Attendance = models.IntegerField(null=True,default=0) 
    Salary_Details = models.IntegerField(null=True,default=0) 

    update_action = models.IntegerField(null=True,default=0) 
    status = models.CharField(max_length=100,null=True,default='New')  


class Fin_Staff_Details(models.Model):
    company_id = models.ForeignKey(Fin_Company_Details, on_delete=models.CASCADE,null=True,blank=True)
    Login_Id = models.ForeignKey(Fin_Login_Details, on_delete=models.CASCADE,null=True,blank=True)
    contact = models.CharField(max_length=255,null=True,blank=True)
    Email = models.CharField(max_length=255,null=True,blank=True) 
    img = models.ImageField(null=True,blank = True,upload_to = 'image/staff')    
    Company_approval_status = models.CharField(max_length=255,null=True,blank=True)

class TrialPeriod(models.Model):
    company = models.OneToOneField(Fin_Company_Details, on_delete=models.CASCADE)
    start_date = models.DateField(auto_now_add=True)
    end_date = models.DateField()
    interested_in_buying = models.IntegerField(default=0)
    feedback = models.TextField(blank=True, null=True)

    def is_active(self):
        return self.end_date >= timezone.now().date()

class Fin_Payment_Terms_updation(models.Model):
    Login_Id = models.ForeignKey(Fin_Login_Details, on_delete=models.CASCADE,null=True,blank=True)
    Payment_Term = models.ForeignKey(Fin_Payment_Terms, on_delete=models.CASCADE,null=True,blank=True)
    status = models.CharField(max_length=100,null=True,default='New') 

class Fin_ANotification(models.Model): 
    Login_Id = models.ForeignKey(Fin_Login_Details, on_delete=models.CASCADE,null=True,blank=True)
    Modules_List = models.ForeignKey(Fin_Modules_List, on_delete=models.CASCADE,null=True,blank=True)
    PaymentTerms_updation = models.ForeignKey(Fin_Payment_Terms_updation, on_delete=models.CASCADE,null=True,blank=True)
    
    Title = models.CharField(max_length=255,null=True,blank=True)
    Discription = models.CharField(max_length=255,null=True,blank=True) 
    Noti_date = models.DateTimeField(auto_now_add=True,null=True)
    date_created = models.DateField(auto_now_add=True,null=True)
    time=models.TimeField(auto_now_add=True,null=True)
    status = models.CharField(max_length=100,null=True,default='New')  

class Fin_DNotification(models.Model): 
    Login_Id = models.ForeignKey(Fin_Login_Details, on_delete=models.CASCADE,null=True,blank=True)
    Distributor_id = models.ForeignKey(Fin_Distributors_Details, on_delete=models.CASCADE,null=True,blank=True)
    Modules_List = models.ForeignKey(Fin_Modules_List, on_delete=models.CASCADE,null=True,blank=True)
    PaymentTerms_updation = models.ForeignKey(Fin_Payment_Terms_updation, on_delete=models.CASCADE,null=True,blank=True)
    
    Title = models.CharField(max_length=255,null=True,blank=True)
    Discription = models.CharField(max_length=255,null=True,blank=True) 
    Noti_date = models.DateTimeField(auto_now_add=True,null=True)
    date_created = models.DateField(auto_now_add=True,null=True)
    time=models.TimeField(auto_now_add=True,null=True)
    status = models.CharField(max_length=100,null=True,default='New')     
   
       
class Fin_Units(models.Model):
    Company = models.ForeignKey(Fin_Company_Details, on_delete=models.CASCADE,null=True)
    name = models.CharField(max_length=100,null=True)

class Fin_Chart_Of_Account(models.Model):
    Company = models.ForeignKey(Fin_Company_Details, on_delete=models.CASCADE, null=True)
    LoginDetails = models.ForeignKey(Fin_Login_Details, on_delete=models.CASCADE, null=True)
    account_type = models.CharField(max_length=255,null=True,blank=True)
    account_name = models.CharField(max_length=255,null=True,blank=True)
    account_code = models.CharField(max_length=255,null=True,blank=True)
    description = models.TextField(null=True,blank=True)
    balance = models.FloatField(null=True, blank=True, default=0.0)
    balance_type = models.CharField(max_length=100,null=True,blank=True)
    credit_card_no = models.CharField(max_length=255,null=True,blank=True)
    sub_account = models.BooleanField(null=True,blank=True, default=False)
    parent_account = models.CharField(max_length=255,null=True,blank=True)
    bank_account_no = models.BigIntegerField(null=True,blank=True)
    date = models.DateField(auto_now_add=True, auto_now=False, null=True, blank=True)
    create_status=models.CharField(max_length=255,null=True,blank=True)
    status = models.CharField(max_length=255,null=True,blank=True)

class Fin_ChartOfAccount_History(models.Model):
    Company = models.ForeignKey(Fin_Company_Details, on_delete=models.CASCADE, null=True)
    LoginDetails = models.ForeignKey(Fin_Login_Details, on_delete=models.CASCADE, null=True)
    account = models.ForeignKey(Fin_Chart_Of_Account, on_delete=models.CASCADE, null=True)
    date = models.DateField(auto_now_add=True, auto_now=False, null=True)
    action_choices = [
        ('Created', 'Created'),
        ('Edited', 'Edited'),
    ]
    action = models.CharField(max_length=20, null=True, blank = True, choices=action_choices)

class Fin_Loan_Term(models.Model):
    duration= models.IntegerField(null=True,blank=True)
    term = models.CharField(max_length=255,null=True,blank=True)
    days = models.IntegerField(null=True,blank=True)
    company = models.ForeignKey(Fin_Company_Details,on_delete=models.CASCADE,null=True,blank=True)


class Fin_Company_Payment_Terms(models.Model):
    Company = models.ForeignKey(Fin_Company_Details, on_delete=models.CASCADE, null=True)
    term_name = models.CharField(max_length=100, null=True)
    days = models.IntegerField(null=True, default=0)


class Fin_CompanyRepeatEvery(models.Model):
    company = models.ForeignKey(Fin_Company_Details, on_delete=models.CASCADE,null=True,blank=True)
    repeat_every = models.CharField(max_length=100,null=True,blank=True) 
    repeat_type = models.CharField(max_length=100,null=True,blank=True) 
    duration = models.IntegerField(null=True,blank=True)
    days = models.IntegerField(null=True,blank=True)


class Fin_Eway_Transportation(models.Model):
    Company = models.ForeignKey('Fin_Company_Details', on_delete=models.CASCADE, null=True)
    LoginDetails = models.ForeignKey('Fin_Login_Details', on_delete=models.CASCADE, null=True)
    
    Name = models.CharField(max_length=200, null= True)
    Type = models.CharField(max_length=100, null=True)


class Stock_Reason(models.Model):
    company = models.ForeignKey(Fin_Company_Details,on_delete=models.CASCADE,null=True,blank=True)
    login_details = models.ForeignKey(Fin_Login_Details,on_delete=models.CASCADE,null=True,blank=True)
    reason = models.CharField(max_length=500)

# ITEMS
class Fin_Items(models.Model):
    Company = models.ForeignKey(Fin_Company_Details, on_delete=models.CASCADE, null=True)
    LoginDetails = models.ForeignKey(Fin_Login_Details, on_delete=models.CASCADE, null=True)
    name = models.CharField(max_length=100,null=True)
    item_type = models.CharField(max_length=100,null=True)
    unit = models.CharField(max_length=100,null=True)
    hsn = models.BigIntegerField(null=True, blank = True)
    sac = models.BigIntegerField(null=True, blank = True)
    tax_reference = models.CharField(max_length=100,null=True)
    intra_state_tax = models.IntegerField(null=True, default=0)
    inter_state_tax = models.IntegerField(null=True, default=0)
    sales_account = models.CharField(max_length=100,null=True)
    selling_price = models.FloatField(null=True, default=0.0)
    sales_description = models.CharField(max_length=100,null=True,blank=True)
    purchase_account = models.CharField(max_length=100,null=True)
    purchase_price = models.FloatField(null=True, default=0.0)
    purchase_description = models.CharField(max_length=100,null=True,blank=True)
    item_created = models.DateField(auto_now_add = True, auto_now = False, null=True)
    min_stock=models.IntegerField(null=True,default=0)
    inventory_account = models.CharField(max_length=100, null=True, blank=True)
    opening_stock = models.IntegerField(null=True, blank=True,default = 0)
    current_stock = models.IntegerField(default=0,blank=True,null=True)
    stock_in = models.IntegerField(default=0,blank=True,null=True)
    stock_out = models.IntegerField(default=0,blank=True,null=True)
    stock_unit_rate= models.FloatField(default=0.0,blank=True,null=True)
    status = models.CharField(max_length=100,null=True, default='Active')


class Fin_Items_Transaction_History(models.Model):
    Company = models.ForeignKey(Fin_Company_Details, on_delete=models.CASCADE, null=True)
    LoginDetails = models.ForeignKey(Fin_Login_Details, on_delete=models.CASCADE, null=True)
    item = models.ForeignKey(Fin_Items, on_delete=models.CASCADE, null=True)
    date = models.DateField(auto_now_add=True, auto_now=False, null=True)
    action_choices = [
        ('Created', 'Created'),
        ('Edited', 'Edited'),
    ]
    action = models.CharField(max_length=20, null=True, blank = True, choices=action_choices)


class Fin_Items_Comments(models.Model):
    Company = models.ForeignKey(Fin_Company_Details, on_delete=models.CASCADE, null=True)
    item = models.ForeignKey(Fin_Items,on_delete=models.CASCADE,null=True,blank=True)
    comments = models.CharField(max_length=500,null=True,blank=True)


# Price List

class Fin_Price_List(models.Model):
    LoginDetails = models.ForeignKey(Fin_Login_Details, on_delete=models.CASCADE,null=True,blank=True)
    Company = models.ForeignKey(Fin_Company_Details, on_delete=models.CASCADE,null=True,blank=True)
    name = models.CharField(max_length=255,null=True,blank=True)
    type = models.CharField(max_length=15,null=True,blank=True,default='Sales')
    item_rate = models.CharField(max_length=100,null=True,blank=True,default='percentage')
    description = models.TextField(blank=True, null=True)
    currency = models.CharField(max_length=255,null=True,blank=True,default='Indian Rupee')
    up_or_down = models.CharField(max_length=100,default='None')
    percentage = models.CharField(max_length=100,null=True,blank=True)
    round_off = models.CharField(max_length=100,default='None', null=True, blank=True)
    created_date = models.DateField(auto_now_add = True, auto_now = False, blank = True, null = True)
    status = models.CharField(max_length=15,default='Active',null=True,blank=True)

# Customers

class Fin_Customers(models.Model):
    Company = models.ForeignKey(Fin_Company_Details, on_delete=models.CASCADE, null=True)
    LoginDetails = models.ForeignKey(Fin_Login_Details, on_delete=models.CASCADE, null=True)
    title = models.CharField(max_length=10,null=True,blank=True)
    first_name = models.CharField(max_length=100,null=True,blank=True)
    last_name = models.CharField(max_length=100,null=True,blank=True)
    company = models.CharField(max_length=100,null=True,blank=True)
    location = models.CharField(max_length=100,null=True,blank=True)
    place_of_supply = models.CharField(max_length=100,null=True,blank=True)
    gst_type = models.CharField(max_length=100, null=True)
    gstin = models.CharField(max_length=100,null=True,blank=True,default=None)
    pan_no = models.CharField(max_length=100, null=True, blank=True)
    email = models.EmailField(null=True,blank=True)
    website = models.CharField(max_length=100, default='',null=True,blank=True)
    mobile = models.CharField(max_length=20,null=True,blank=True)
    price_list = models.ForeignKey(Fin_Price_List, on_delete = models.SET_NULL, null = True)
    payment_terms = models.ForeignKey(Fin_Company_Payment_Terms, on_delete = models.SET_NULL,null=True)
    billing_street = models.CharField(max_length=100,null=True,blank=True)
    billing_city = models.CharField(max_length=100,null=True,blank=True)
    billing_state = models.CharField(max_length=100,null=True,blank=True)
    billing_pincode = models.CharField(max_length=100,null=True,blank=True)
    billing_country = models.CharField(max_length=100,null=True,blank=True)
    ship_street = models.CharField(max_length=100,null=True,blank=True)
    ship_city = models.CharField(max_length=100,null=True,blank=True)
    ship_state = models.CharField(max_length=100,null=True,blank=True)
    ship_pincode = models.CharField(max_length=100,null=True,blank=True)
    ship_country = models.CharField(max_length=100,null=True,blank=True)
    opening_balance = models.FloatField(null=True, blank=True, default=0.0)
    opening_balance_due = models.FloatField(null=True, blank=True, default=0.0)
    open_balance_type = models.CharField(max_length=100,null=True,blank=True)
    current_balance = models.FloatField(null=True, blank=True, default=0.0)
    credit_limit = models.FloatField(null=True, blank=True, default=0.0)
    date = models.DateField(null=True, auto_now_add=True,auto_now=False)
    customer_status = (
        ('Active','Active'),
        ('Inactive','Inactive'),
    )
    status =models.CharField(max_length=150,choices=customer_status,default='Active',null=True,blank=True)

class Fin_Customers_History(models.Model):
    Company = models.ForeignKey(Fin_Company_Details, on_delete=models.CASCADE, null=True)
    LoginDetails = models.ForeignKey(Fin_Login_Details, on_delete=models.CASCADE, null=True)
    customer = models.ForeignKey(Fin_Customers,on_delete=models.CASCADE,null=True,blank=True)
    date = models.DateField(auto_now_add=True, auto_now=False, null=True)
    action_choices = [
        ('Created', 'Created'),
        ('Edited', 'Edited'),
    ]
    action = models.CharField(max_length=20, null=True, blank = True, choices=action_choices)


class Fin_Customers_Comments(models.Model):
    Company = models.ForeignKey(Fin_Company_Details, on_delete=models.CASCADE, null=True)
    customer = models.ForeignKey(Fin_Customers,on_delete=models.CASCADE,null=True,blank=True)
    comments = models.CharField(max_length=500,null=True,blank=True)


class Fin_CNotification(models.Model): 
    Login_Id = models.ForeignKey(Fin_Login_Details, on_delete=models.CASCADE,null=True,blank=True)
    Company_id = models.ForeignKey(Fin_Company_Details, on_delete=models.CASCADE,null=True,blank=True)
    Item = models.ForeignKey(Fin_Items, on_delete = models.CASCADE, null=True, blank=True) # Added - shemeem -> Handle Item's min stock alerts
    Customers = models.ForeignKey(Fin_Customers, on_delete = models.CASCADE, null=True,blank=True) # Added - shemeem -> Handle customer's credit limit alerts
    # Vendors = models.ForeignKey(Fin_Vendors, on_delete = models.CASCADE, null=True,blank=True) # Added - shemeem -> Handle vendor's credit limit alerts
    
    Title = models.CharField(max_length=255,null=True,blank=True)
    Discription = models.CharField(max_length=255,null=True,blank=True) 
    Noti_date = models.DateTimeField(auto_now_add=True,null=True)
    date_created = models.DateField(auto_now_add=True,null=True)
    time=models.TimeField(auto_now_add=True,null=True)
    status = models.CharField(max_length=100,null=True,default='New')   
    
    
class Fin_PriceList_Items(models.Model):
    LoginDetails = models.ForeignKey(Fin_Login_Details, on_delete=models.CASCADE,null=True,blank=True)
    Company = models.ForeignKey(Fin_Company_Details, on_delete=models.CASCADE,null=True,blank=True)
    list = models.ForeignKey(Fin_Price_List,on_delete=models.CASCADE,null=True,blank=True)
    item = models.ForeignKey(Fin_Items,on_delete=models.CASCADE,null=True,blank=True)
    standard_rate = models.FloatField(null=True,blank=True,default=0.0)
    custom_rate=models.FloatField(null=True,blank=True,default=0.0)


class Fin_PriceList_Transaction_History(models.Model):
    Company = models.ForeignKey(Fin_Company_Details, on_delete=models.CASCADE, null=True)
    LoginDetails = models.ForeignKey(Fin_Login_Details, on_delete=models.CASCADE, null=True)
    list = models.ForeignKey(Fin_Price_List,on_delete=models.CASCADE,null=True,blank=True)
    date = models.DateField(auto_now_add=True, auto_now=False, null=True)
    action_choices = [
        ('Created', 'Created'),
        ('Edited', 'Edited'),
    ]
    action = models.CharField(max_length=20, null=True, blank = True, choices=action_choices)


class Fin_PriceList_Comments(models.Model):
    Company = models.ForeignKey(Fin_Company_Details, on_delete=models.CASCADE, null=True)
    list = models.ForeignKey(Fin_Price_List,on_delete=models.CASCADE,null=True,blank=True)
    comments = models.CharField(max_length=500,null=True,blank=True)
    
# Banking
class Fin_Banking(models.Model):
    login_details = models.ForeignKey(Fin_Login_Details, on_delete=models.CASCADE,null=True,blank=True)
    company = models.ForeignKey(Fin_Company_Details, on_delete=models.CASCADE,null=True,blank=True)

    bank_name = models.CharField(max_length=255,null=True,blank=True) 
    account_number = models.CharField(max_length=255,null=True,blank=True) 
    ifsc_code = models.CharField(max_length=255,null=True,blank=True) 
    branch_name = models.CharField(max_length=255,null=True,blank=True) 
    opening_balance_type = models.CharField(max_length=255,null=True,blank=True) 
    opening_balance = models.IntegerField(null=True,default=0)
    date = models.DateTimeField(auto_now_add=False,null=True)
    current_balance = models.IntegerField(null=True,default=0)
    bank_status = models.CharField(max_length=255,null=True,blank=True) 
   
class Fin_BankingHistory(models.Model):
    login_details = models.ForeignKey(Fin_Login_Details, on_delete=models.CASCADE,null=True,blank=True)
    company = models.ForeignKey(Fin_Company_Details, on_delete=models.CASCADE,null=True,blank=True)
    banking = models.ForeignKey(Fin_Banking, on_delete=models.CASCADE,null=True,blank=True)
    date = models.DateTimeField(auto_now_add=True,null=True)
    action = models.CharField(max_length=255,null=True,blank=True)

class Fin_BankingAttachments(models.Model): 

    login_details = models.ForeignKey(Fin_Login_Details, on_delete=models.CASCADE,null=True,blank=True)
    company = models.ForeignKey(Fin_Company_Details, on_delete=models.CASCADE,null=True,blank=True)
    banking = models.ForeignKey(Fin_Banking, on_delete=models.CASCADE,null=True,blank=True)
    date = models.DateTimeField(auto_now_add=True,null=True)
    file = models.ImageField(null=True,blank = True,upload_to = 'image/banking')
    
class Fin_BankingComments(models.Model): 

    login_details = models.ForeignKey(Fin_Login_Details, on_delete=models.CASCADE,null=True,blank=True)
    company = models.ForeignKey(Fin_Company_Details, on_delete=models.CASCADE,null=True,blank=True)
    banking = models.ForeignKey(Fin_Banking, on_delete=models.CASCADE,null=True,blank=True)
    date = models.DateTimeField(auto_now_add=True,null=True)
    comment = models.CharField(max_length=255,null=True,blank=True)
    
class Fin_BankTransactions(models.Model): 

    login_details = models.ForeignKey(Fin_Login_Details, on_delete=models.CASCADE,null=True,blank=True)
    company = models.ForeignKey(Fin_Company_Details, on_delete=models.CASCADE,null=True,blank=True)
    banking = models.ForeignKey(Fin_Banking, on_delete=models.CASCADE,null=True,blank=True)

    from_type = models.CharField(max_length=255,null=True,blank=True) 
    to_type = models.CharField(max_length=255,null=True,blank=True) 
    amount = models.IntegerField(null=True,default=0)
    adjustment_date = models.DateTimeField(auto_now_add=False,null=True)
    description = models.CharField(max_length=255,null=True,blank=True) 
    transaction_type = models.CharField(max_length=255,null=True,blank=True) 
    adjustment_type = models.CharField(max_length=255,null=True,blank=True) 
    current_balance = models.IntegerField(null=True,default=0)
    bank_to_bank = models.IntegerField(null=True,default=0)
    
class Fin_BankTransactionHistory(models.Model): 

    login_details = models.ForeignKey(Fin_Login_Details, on_delete=models.CASCADE,null=True,blank=True)
    company = models.ForeignKey(Fin_Company_Details, on_delete=models.CASCADE,null=True,blank=True)
    bank_transaction = models.ForeignKey(Fin_BankTransactions, on_delete=models.CASCADE,null=True,blank=True)
    date = models.DateTimeField(auto_now_add=True,null=True)
    action = models.CharField(max_length=255,null=True,blank=True)
#End

#employee
class Employee(models.Model):
    upload_file = models.FileField(upload_to='file/',blank=True) 
    upload_image = models.ImageField(upload_to='media/',blank=True)
    title = models.CharField(max_length=255,null=True,blank=True)
    first_name = models.CharField(max_length=255,null=True,blank=True)
    last_name = models.CharField(max_length=255,null=True,blank=True)
    alias = models.CharField(max_length=255,null=True,blank=True)
    employee_mail = models.EmailField(null=True,blank=True)
    employee_number = models.CharField(max_length=255,null=True,blank=True)
    employee_designation = models.CharField(max_length=255,null=True,blank=True)
    function = models.CharField(max_length=255,null=True,blank=True)
    employee_current_location = models.CharField(max_length=255,null=True,blank=True)
    mobile = models.CharField(max_length=255,null=True,blank=True)
    date_of_joining = models.DateField(null=True,blank=True)
    employee_salary_type = models.CharField(max_length=255,null=True,blank=True)
    salary_details = models.CharField(max_length=10,null=True,blank=True)
    salary_effective_from = models.CharField(max_length=255,null=True,blank=True)

    pay_head = models.CharField(max_length=255,null=True,blank=True)
    salary_amount = models.FloatField(null=True,blank=True)
    amount_per_hour = models.IntegerField(null=True,blank=True)
    total_working_hours = models.IntegerField(null=True,blank=True)
    gender = models.CharField(max_length=255,null=True,blank=True)
    date_of_birth = models.DateField(null=True,blank=True)
    age = models.IntegerField(null=True,blank=True)
    blood_group = models.CharField(max_length=255,null=True,blank=True)
    fathers_name_mothers_name = models.CharField(max_length=255,null=True,blank=True)
    spouse_name = models.CharField(max_length=255,null=True,blank=True)
    emergency_contact = models.CharField(max_length=255,null=True,blank=True)
    provide_bank_details = models.CharField(max_length=255,null=True,blank=True)
    account_number = models.CharField(max_length=255,null=True,blank=True)
    ifsc = models.CharField(max_length=255,null=True,blank=True)
    name_of_bank = models.CharField(max_length=255,null=True,blank=True)
    branch_name = models.CharField(max_length=255,null=True,blank=True)
    bank_transaction_type = models.CharField(max_length=255,null=True,blank=True)
    tds_applicable = models.CharField(max_length=255,null=True,blank=True)
    tds_type = models.CharField(max_length=255,null=True,blank=True)
    percentage_amount = models.IntegerField(null=True,blank=True)
    pan_number = models.CharField(max_length=255,null=True,blank=True)
    income_tax_number = models.CharField(max_length=255,null=True,blank=True)
    aadhar_number = models.CharField(max_length=255,null=True,blank=True)
    universal_account_number = models.CharField(max_length=255,null=True,blank=True)
    pf_account_number = models.CharField(max_length=255,null=True,blank=True)
    pr_account_number = models.CharField(max_length=255,null=True,blank=True)
    esi_number = models.CharField(max_length=255,null=True,blank=True)

    street = models.CharField(max_length=255,null=True,blank=True)
    city = models.CharField(max_length=255,null=True,blank=True)
    state = models.CharField(max_length=255,null=True,blank=True)
    pincode = models.CharField(max_length=255,null=True,blank=True)
    country = models.CharField(max_length=255,null=True,blank=True)
    temporary_street = models.CharField(max_length=255,null=True,blank=True)
    temporary_city = models.CharField(max_length=255,null=True,blank=True)
    temporary_state = models.CharField(max_length=255,null=True,blank=True)
    temporary_pincode = models.CharField(max_length=255,null=True,blank=True)
    temporary_country = models.CharField(max_length=255,null=True,blank=True)
    employee_status = models.CharField(max_length=30,null=True,blank=True)
    company = models.ForeignKey(Fin_Company_Details,on_delete=models.CASCADE,null=True,blank=True)
    login = models.ForeignKey(Fin_Login_Details,on_delete=models.CASCADE,null=True,blank=True)

class Employee_History(models.Model):
    company = models.ForeignKey(Fin_Company_Details,on_delete=models.CASCADE,null=True,blank=True)
    login = models.ForeignKey(Fin_Login_Details,on_delete=models.CASCADE,null=True,blank=True)
    employee = models.ForeignKey(Employee,on_delete=models.CASCADE,blank=True,null=True)
    date = models.DateField(null=True,blank=True)
    action = models.CharField(max_length=255,null=True,blank=True)

class Employee_Comment(models.Model):
    employee = models.ForeignKey(Employee,on_delete=models.CASCADE,blank=True,null=True)
    company = models.ForeignKey(Fin_Company_Details,on_delete=models.CASCADE,null=True,blank=True)
    login = models.ForeignKey(Fin_Login_Details,on_delete=models.CASCADE,null=True,blank=True)
    comment = models.CharField(max_length=255,null=True,blank=True)
    date = models.DateField(default = date.today())
    
class Employee_Blood_Group(models.Model):
    blood_group = models.CharField(max_length=255,null=True,blank=True)
    company = models.ForeignKey(Fin_Company_Details,on_delete=models.CASCADE,null=True,blank=True)
    login = models.ForeignKey(Fin_Login_Details,on_delete=models.CASCADE,null=True,blank=True)      

#End
# Stock Adjustment

class Stock_Adjustment(models.Model):
    company = models.ForeignKey(Fin_Company_Details,on_delete=models.CASCADE,null=True,blank=True)
    login_details = models.ForeignKey(Fin_Login_Details,on_delete=models.CASCADE,null=True,blank=True)
    mode_of_adjustment = models.CharField(max_length=255,null=True,blank=True)
    reference_no = models.BigIntegerField(null=True,blank=True)
    adjusting_date = models.DateField(null=True,blank=True)
    account = models.CharField(max_length=255,null=True,blank=True)
    reason = models.CharField(max_length=255,null=True,blank=True)
    description = models.CharField(max_length=255,null=True,blank=True)
    attach_file = models.FileField(upload_to='file/stock_adj/',blank=True)
    status=models.CharField(max_length=255,null=True,blank=True)

class Stock_Adjustment_Items(models.Model):
    company = models.ForeignKey(Fin_Company_Details,on_delete=models.CASCADE,null=True,blank=True)
    login_details = models.ForeignKey(Fin_Login_Details,on_delete=models.CASCADE,null=True,blank=True)
    item= models.ForeignKey(Fin_Items,on_delete=models.CASCADE,null=True,blank=True)
    stock_adjustment=models.ForeignKey(Stock_Adjustment,on_delete=models.CASCADE,null=True,blank=True)
    quantity_avail = models.DecimalField(max_digits=10, decimal_places=2,null=True,blank=True)
    quantity_inhand = models.DecimalField(max_digits=10, decimal_places=2,null=True,blank=True)
    quantity_adj = models.DecimalField(max_digits=10, decimal_places=2,null=True,blank=True)
    current_val = models.DecimalField(max_digits=10, decimal_places=2,null=True,blank=True)
    changed_val = models.DecimalField(max_digits=10, decimal_places=2,null=True,blank=True)
    adjusted_val = models.DecimalField(max_digits=10, decimal_places=2,null=True,blank=True)
    type=models.CharField(max_length=255,null=True,blank=True,default='None')

class Stock_Adjustment_History(models.Model):
    company = models.ForeignKey(Fin_Company_Details,on_delete=models.CASCADE,null=True,blank=True)
    login_details = models.ForeignKey(Fin_Login_Details,on_delete=models.CASCADE,null=True,blank=True)
    item= models.ForeignKey(Fin_Items,on_delete=models.CASCADE,null=True,blank=True)
    date = models.DateField(null=True,blank=True)
    action = models.CharField(max_length=255,null=True,blank=True)
    stock_adjustment=models.ForeignKey(Stock_Adjustment,on_delete=models.CASCADE,null=True,blank=True)

class Stock_Adjustment_Comment(models.Model):
    company = models.ForeignKey(Fin_Company_Details,on_delete=models.CASCADE,null=True,blank=True)
    login_details = models.ForeignKey(Fin_Login_Details,on_delete=models.CASCADE,null=True,blank=True)
    stock_adjustment=models.ForeignKey(Stock_Adjustment,on_delete=models.CASCADE,null=True,blank=True)
    comment = models.CharField(max_length=500,default='None')
  
class Stock_Adjustment_RefNo(models.Model):
    company = models.ForeignKey(Fin_Company_Details,on_delete=models.CASCADE,null=True,blank=True)
    login_details = models.ForeignKey(Fin_Login_Details,on_delete=models.CASCADE,null=True,blank=True)
    reference_no = models.BigIntegerField(null = False, blank=False)


# Sales Order
class Fin_Sales_Order(models.Model):
    Company = models.ForeignKey(Fin_Company_Details, on_delete=models.CASCADE, null=True)
    LoginDetails = models.ForeignKey(Fin_Login_Details, on_delete=models.CASCADE, null=True)
    Customer = models.ForeignKey(Fin_Customers, on_delete=models.CASCADE, null=True)
    customer_email = models.EmailField(max_length=100, null=True, blank=True)
    billing_address = models.TextField(null=True, blank=True)
    gst_type = models.CharField(max_length=100, null=True, blank=True)
    gstin = models.CharField(max_length=100, null=True, blank=True)
    place_of_supply = models.CharField(max_length=100, null=True, blank=True)
    reference_no = models.IntegerField(null=True, blank=True)
    sales_order_no = models.CharField(max_length=100)
    payment_terms = models.ForeignKey(Fin_Company_Payment_Terms, on_delete = models.SET_NULL,null=True)
    sales_order_date = models.DateField(null=True, blank=True)
    exp_ship_date = models.DateField(null=True,blank=True)
    price_list_applied = models.BooleanField(null=True, default=False)
    price_list = models.ForeignKey(Fin_Price_List, on_delete = models.SET_NULL,null=True)

    payment_method = models.CharField(max_length=100, null=True, blank=True)
    cheque_no = models.CharField(max_length=100, null=True, blank=True)
    upi_no = models.CharField(max_length=100, null=True, blank=True)
    bank_acc_no = models.CharField(max_length=100, null=True, blank=True)

    subtotal = models.FloatField(default=0.0, null=True)
    igst = models.FloatField(default=0.0, null=True, blank=True)
    cgst = models.FloatField(default=0.0, null=True, blank=True)
    sgst = models.FloatField(default=0.0, null=True, blank=True)
    tax_amount = models.FloatField(default=0.0, null=True, blank=True)
    adjustment = models.FloatField(default=0.0, null=True, blank=True)
    shipping_charge = models.FloatField(default=0.0, null=True, blank=True)
    grandtotal = models.FloatField(default=0.0, null=True, blank=True)
    paid_off = models.FloatField(default=0.0, null=True, blank=True)
    balance = models.FloatField(default=0.0, null=True, blank=True)

    # converted_from_estimate = models.ForeignKey(Fin_Estimate, on_delete = models.SET_NULL, null = True)
    # converted_to_invoice =  models.ForeignKey(Fin_Invoice, on_delete = models.SET_NULL, null = True)
    # converted_to_rec_invoice =  models.ForeignKey(Fin_Recurring_Invoice, on_delete = models.SET_NULL, null = True)
    
    note = models.TextField(null=True, blank=True)
    file = models.FileField(upload_to='sales_order', null=True, default=None)
    status =models.CharField(max_length=150,default='Draft')

    def getNumFieldName(self):
        return 'sales_order_no'


class Fin_Sales_Order_Items(models.Model):
    SalesOrder = models.ForeignKey(Fin_Sales_Order,on_delete=models.CASCADE, null=True)
    Item = models.ForeignKey(Fin_Items,on_delete=models.SET_NULL, null=True)
    hsn = models.IntegerField(null=True, blank=True)
    sac = models.IntegerField(null=True, blank=True)
    quantity = models.IntegerField(default=0, null=True)
    price = models.FloatField(default=0.0, null=True, blank=True)
    total = models.FloatField(default=0.0, null=True, blank=True)
    tax = models.CharField(max_length=100, null=True)
    discount = models.FloatField(default=0.0, null=True, blank=True)


class Fin_Sales_Order_Reference(models.Model):
    Company = models.ForeignKey(Fin_Company_Details, on_delete=models.CASCADE, null=True)
    LoginDetails = models.ForeignKey(Fin_Login_Details, on_delete=models.CASCADE, null=True)
    reference_no = models.BigIntegerField(null = False, blank=False)


class Fin_Sales_Order_History(models.Model):
    Company = models.ForeignKey(Fin_Company_Details, on_delete=models.CASCADE, null=True)
    LoginDetails = models.ForeignKey(Fin_Login_Details, on_delete=models.CASCADE, null=True)
    SalesOrder = models.ForeignKey(Fin_Sales_Order,on_delete=models.CASCADE, null=True)
    date = models.DateField(auto_now_add=True, auto_now=False, null=True)
    action_choices = [
        ('Created', 'Created'),
        ('Edited', 'Edited'),
    ]
    action = models.CharField(max_length=20, null=True, blank = True, choices=action_choices)


class Fin_Sales_Order_Comments(models.Model):
    Company = models.ForeignKey(Fin_Company_Details, on_delete=models.CASCADE, null=True)
    SalesOrder = models.ForeignKey(Fin_Sales_Order,on_delete=models.CASCADE, null=True)
    comments = models.CharField(max_length=500,null=True,blank=True)
#End
# Vendors
class Fin_Vendor(models.Model):
    Title = models.CharField(max_length=10,null=True)
    First_name = models.CharField(max_length=50,null=True)
    Last_name = models.CharField(max_length=50,null=True)
    Vendor_email = models.EmailField(null=True)
    Mobile = models.CharField(max_length=25,null=True)
    Company_Name = models.CharField(max_length=100,null=True)
    Location = models.CharField(max_length=100,null=True)
    Website = models.CharField(max_length=100,null=True,default='')
    GST_Treatment = models.CharField(max_length=50,null=True)
    GST_Number = models.CharField(max_length=50,null=True)
    Pan_Number = models.CharField(max_length=50,null=True)
    Opening_balance_type = models.CharField(max_length=50,null=True)
    Opening_balance = models.FloatField(null=True,default=0.0)
    Current_balance = models.FloatField(null=True,default=0.0)
    Credit_limit = models.FloatField(null=True,default=0.0)
    Place_of_supply = models.CharField(max_length=200,null=True)
    Billing_street = models.CharField(max_length=200,null=True)
    Billing_city = models.CharField(max_length=200,null=True)
    Billing_state = models.CharField(max_length=200,null=True)
    Billing_country = models.CharField(max_length=200,null=True)
    Billing_pincode = models.CharField(max_length=10,null=True)
    Shipping_street = models.CharField(max_length=200,null=True)
    Shipping_city = models.CharField(max_length=200,null=True)
    Shipping_state = models.CharField(max_length=200,null=True)
    Shipping_country = models.CharField(max_length=200,null=True)
    Shipping_pincode = models.CharField(max_length=10,null=True)
    currency = models.CharField(max_length=50,null=True)
    Date = models.DateField(auto_now_add=True,auto_now=False,null=True)
    vendor_status = (
        ('Active','Active'),
        ('Inactive','Inactive'),
    )
    status = models.CharField(max_length=100,null=True,choices=vendor_status,default='Active')
    payment_terms = models.ForeignKey(Fin_Company_Payment_Terms,on_delete=models.CASCADE,null=True)
    Company = models.ForeignKey(Fin_Company_Details,on_delete=models.CASCADE,null=True)
    Login_details = models.ForeignKey(Fin_Login_Details,on_delete=models.CASCADE,null=True)

class Fin_Vendor_History(models.Model):
    Company = models.ForeignKey(Fin_Company_Details,on_delete=models.CASCADE,null=True)
    Login_details = models.ForeignKey(Fin_Login_Details,on_delete=models.CASCADE,null=True)
    Vendor = models.ForeignKey(Fin_Vendor,on_delete=models.CASCADE,null=True)
    Date = models.DateField(auto_now_add=True,auto_now=False,null=True)
    Action_choices = (
        ('Created', 'Created'),
        ('Edited', 'Edited'),
    )
    Action = models.CharField(max_length=30,null=True,choices=Action_choices)

class Fin_Vendor_Comments(models.Model):
    Company = models.ForeignKey(Fin_Company_Details,on_delete=models.CASCADE,null=True)
    Vendor = models.ForeignKey(Fin_Vendor,on_delete=models.CASCADE,null=True)
    comments = models.CharField(max_length=200,null=True)
    
#End

# Purchase Order
class Fin_Purchase_Order(models.Model):
    Company = models.ForeignKey(Fin_Company_Details, on_delete=models.CASCADE, null=True)
    LoginDetails = models.ForeignKey(Fin_Login_Details, on_delete=models.CASCADE, null=True)

    Vendor = models.ForeignKey(Fin_Vendor, on_delete=models.CASCADE, null=True)
    vendor_name = models.CharField(max_length=200, null=True, blank=True)
    vendor_email = models.EmailField(max_length=100, null=True, blank=True)
    vendor_address = models.TextField(null=True, blank=True)
    vendor_gst_type = models.CharField(max_length=100, null=True, blank=True)
    vendor_gstin = models.CharField(max_length=100, null=True, blank=True)
    vendor_source_of_supply = models.CharField(max_length=100, null=True, blank=True)

    reference_no = models.IntegerField(null=True, blank=True)
    purchase_order_no = models.CharField(max_length=100)
    payment_terms = models.ForeignKey(Fin_Company_Payment_Terms, on_delete = models.SET_NULL,null=True)
    purchase_order_date = models.DateField(null=True, blank=True)
    due_date = models.DateField(null=True,blank=True)

    payment_method = models.CharField(max_length=100, null=True, blank=True)
    cheque_no = models.CharField(max_length=100, null=True, blank=True)
    upi_no = models.CharField(max_length=100, null=True, blank=True)
    bank_acc_no = models.CharField(max_length=100, null=True, blank=True)

    Customer = models.ForeignKey(Fin_Customers, on_delete=models.CASCADE, null=True)
    customer_name = models.CharField(max_length=200, null=True, blank=True)
    customer_email = models.EmailField(max_length=100, null=True, blank=True)
    customer_address = models.TextField(null=True, blank=True)
    customer_gst_type = models.CharField(max_length=100, null=True, blank=True)
    customer_gstin = models.CharField(max_length=100, null=True, blank=True)
    customer_place_of_supply = models.CharField(max_length=100, null=True, blank=True)

    price_list_applied = models.BooleanField(null=True, default=False)
    price_list = models.ForeignKey(Fin_Price_List, on_delete = models.SET_NULL,null=True)

    subtotal = models.FloatField(default=0.0, null=True)
    igst = models.FloatField(default=0.0, null=True, blank=True)
    cgst = models.FloatField(default=0.0, null=True, blank=True)
    sgst = models.FloatField(default=0.0, null=True, blank=True)
    tax_amount = models.FloatField(default=0.0, null=True, blank=True)
    adjustment = models.FloatField(default=0.0, null=True, blank=True)
    shipping_charge = models.FloatField(default=0.0, null=True, blank=True)
    grandtotal = models.FloatField(default=0.0, null=True, blank=True)
    paid_off = models.FloatField(default=0.0, null=True, blank=True)
    balance = models.FloatField(default=0.0, null=True, blank=True)

    # converted_to_bill =  models.ForeignKey(Fin_Purchase_Bill, on_delete = models.SET_NULL, null = True)
    # converted_to_rec_bill =  models.ForeignKey(Fin_Recurring_Bills, on_delete = models.SET_NULL, null = True)
    
    note = models.TextField(null=True, blank=True)
    file = models.FileField(upload_to='purchase_order', null=True, default=None)
    status =models.CharField(max_length=150,default='Draft')

    def getNumFieldName(self):
        return 'purchase_order_no'
    
class Fin_Purchase_Order_Items(models.Model):
    PurchaseOrder = models.ForeignKey(Fin_Purchase_Order,on_delete=models.CASCADE, null=True)
    Item = models.ForeignKey(Fin_Items,on_delete=models.SET_NULL, null=True)
    hsn = models.IntegerField(null=True, blank=True)
    sac = models.IntegerField(null=True, blank=True)
    quantity = models.IntegerField(default=0, null=True)
    price = models.FloatField(default=0.0, null=True, blank=True)
    total = models.FloatField(default=0.0, null=True, blank=True)
    tax = models.CharField(max_length=100, null=True)
    discount = models.FloatField(default=0.0, null=True, blank=True)


class Fin_Purchase_Order_Reference(models.Model):
    Company = models.ForeignKey(Fin_Company_Details, on_delete=models.CASCADE, null=True)
    LoginDetails = models.ForeignKey(Fin_Login_Details, on_delete=models.CASCADE, null=True)
    reference_no = models.BigIntegerField(null = False, blank=False)


class Fin_Purchase_Order_History(models.Model):
    Company = models.ForeignKey(Fin_Company_Details, on_delete=models.CASCADE, null=True)
    LoginDetails = models.ForeignKey(Fin_Login_Details, on_delete=models.CASCADE, null=True)
    PurchaseOrder = models.ForeignKey(Fin_Purchase_Order,on_delete=models.CASCADE, null=True)
    date = models.DateField(auto_now_add=True, auto_now=False, null=True)
    action_choices = [
        ('Created', 'Created'),
        ('Edited', 'Edited'),
    ]
    action = models.CharField(max_length=20, null=True, blank = True, choices=action_choices)


class Fin_Purchase_Order_Comments(models.Model):
    Company = models.ForeignKey(Fin_Company_Details, on_delete=models.CASCADE, null=True)
    PurchaseOrder = models.ForeignKey(Fin_Purchase_Order,on_delete=models.CASCADE, null=True)
    comments = models.CharField(max_length=500,null=True,blank=True)