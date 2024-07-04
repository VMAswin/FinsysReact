import React, { useEffect, useState } from "react";
import FinBase from "../FinBase";
import { Link, useNavigate } from "react-router-dom";
import Cookies from "js-cookie";
import axios from "axios";
import config from "../../../functions/config";
import Swal from "sweetalert2";
import Select from "react-select";

function Add_Purchase_Order () {
  const ID = Cookies.get("Login_id");
  const navigate = useNavigate();
  const [items, setItems] = useState([]);
  const [vendors, setVendors] = useState([]);
  const [terms, setTerms] = useState([]);
  const [banks, setBanks] = useState([]);
  const [priceLists, setPriceLists] = useState([]);
  const [customerPriceLists, setCustomerPriceLists] = useState([]);
  const [cmpState, setCmpState] = useState("");

  const customStyles = {
      control: (provided) => ({
        ...provided,
        backgroundColor: "rgb(255 255 255 / 14%)",
      }),
      singleValue: (provided, state) => ({
        ...provided,
        color: "white",
      }),
      menu: (provided) => ({
        ...provided,
        backgroundColor: "white",
      }),
      option: (provided, state) => ({
        ...provided,
        backgroundColor: state.isSelected
          ? "lightgray"
          : state.isFocused
          ? "lightgray"
          : "white",
        color: state.isSelected ? "black" : "black",
      }),
      input: (provided) => ({
        ...provided,
        color: "white",
      }),
      placeholder: (provided) => ({
        ...provided,
        color: "white",
      }),
    };

  const fetchPaymentTerms = () => {
      axios
        .get(`${config.base_url}/get_company_payment_terms/${ID}/`)
        .then((res) => {
          console.log("PTERMS==", res);
          if (res.data.status) {
            let pTrms = res.data.terms;
            setTerms([]);
            pTrms.map((i) => {
              setTerms((prevState) => [...prevState, i]);

            });
          }
        })
        .catch((err) => {
          console.log(err);
        });
    };
    useEffect(() => {
      fetchPaymentTerms();
    }, []);
    
    const fetchitems = () => {
      axios
        .get(`${config.base_url}/fetch_items/${ID}/`)
        .then((res) => {
          console.log("ITEMS==", res);
          if (res.data.status) {
            let item = res.data.items;
            setItems(item);
            // setItems([]);
            // item.map((i) => {
            //   setItems((prevState) => [...prevState, i]);

            // });
          }
        })
        .catch((err) => {
          console.log(err);
        });
    };
    useEffect(() => {
      fetchitems();
    }, []);

    const fetchVendors = () => {
      axios
        .get(`${config.base_url}/fetch_vendors/${ID}/`)
        .then((res) => {
          if (res.data.status) {
            let vendor = res.data.vendors;
            setVendors([]);
            vendor.map((i) => {
              setVendors((prevState) => [...prevState, i]);

            });
          }
        })
        .catch((err) => {
          console.log(err);
        });
    };
    useEffect(() => {
      fetchVendors();
    }, []);

    const [email, setEmail] = useState([]);
    const [address ,setAddress] = useState([]);
    const [name,setName] = useState([]);
    const [gst_type,setGstType] = useState([]);
    const [place_of_supply,setPlaceOfSupply] = useState([]);
    const [gstIN,setGstIn] = useState([]);
    const getVendorDetails = (id) =>{
      axios
        .get(`${config.base_url}/get_vendor_details/${id}/`)
        .then((res) => {
          if (res.data.status) {
            let vendor = res.data.vendorDetails;
            setEmail(vendor.email);
            setAddress(vendor.address);
            setName(vendor.name);
            setGstType(vendor.gstType);
            setGstIn(vendor.gstIn);
            setPlaceOfSupply(vendor.placeOfSupply);
          }
        })
        .catch((err) => {
          console.log(err);
        });
    };
    const [customers,setCustomer] = useState([]);
    const getCustomers = () => {
      axios
        .get(`${config.base_url}/fetch_customers/${ID}/`)
        .then((res) => {
          if (res.data.status) {
            let customer = res.data.customers;
            setCustomer([]);
            customer.map((i) => {
              setCustomer((prevState) => [...prevState, i]);

            });
          }
        })
        .catch((err) => {
          console.log(err);
        });
    };
    useEffect(() =>{
      getCustomers();
    },[]);
    const [cemail, setCEmail] = useState([]);
    const [caddress ,setCAddress] = useState([]);
    const [cname,setCName] = useState([]);
    const [cgst_type,setCGstType] = useState([]);
    const [cplace_of_supply,setCPlaceOfSupply] = useState([]);
    const [cgstIN,setCGstIn] = useState([]);
    const get_customer_details = (id) =>{
      axios
        .get(`${config.base_url}/get_customer_details/${id}/`)
        .then((res) => {
          if (res.data.status) {
            let customer = res.data.customerDetails;
            setCEmail(customer.email);
            setCAddress(customer.address);
            setCName(customer.name);
            setCGstType(customer.gstType);
            setCGstIn(customer.gstIn);
            setCPlaceOfSupply(customer.placeOfSupply);
          }
        })
        .catch((err) => {
          console.log(err);
        });
    };


    return (
        <>
        <FinBase />
        <form action="{% url 'Fin_createPurchaseOrder' %}" method="post" className="needs-validation" enctype="multipart/form-data" onsubmit="return validateForm()" style={{backgroundColor:'#2f516f'}}>
  
  <div className="page-content py-0 my-0" style={{ backgroundColor: "#2f516f", minHeight: "100vh" }}>

    <div className="d-flex justify-content-end mb-1">
        <a href="{% url 'Fin_purchaseOrder' %}"><i className="fa fa-times-circle text-white mx-4 p-1" style={{fontSize:'1.2rem',marginRight:'-0rem !important'}}></i></a>
      </div>
    <div className="card radius-15 h-20">
        <div className="row">
          <div className="col-md-12">
            <center><h2 className="mt-3">PURCHASE ORDER</h2></center>
            <hr/>
          </div>
        </div>
      </div>

    {/* <!-- <span className="d-flex justify-content-end p-2" style="cursor: pointer;" onclick="window.location.href=`{% url 'Fin_purchaseOrder' %}`"><i className="fa fa-times-circle text-white" style="font-size: 1.2rem;"></i></span>
    <div className="card radius-15">
      <div className="card-body">
        <div className="card-title">
          <center><h3 className="mb-0">PURCHASE ORDER</h3></center>
        </div>
        <hr />
      </div>
    </div> --> */}
    <div className="card radius-15">
      <div className="card-body">
        <div id="purchaseOrder">
            <div className="card-title">
                <h4 className="mb-0">Vendor Details</h4>
            </div>
            <hr/>
            <div className="row">
                <div className="col-md-4 mt-3">
                    <label className="">Select Vendor</label><span className="text-danger ml-3" id="vendErr"></span>
                    <input type="hidden" name="vendorId" id="vendorId" value="" />
                    <div className="d-flex">
                        <div className="w-100">
                            <div className="p-0 border-0 bg-none position-relative drop-box" style={{display:'block'}}>
                            <input required type="text" id="vendorInp" name="vendor" class="dropdown-toggle form-control vendors-display" onkeyup="filterVendors()" data-toggle="dropdown" aria-expanded="false" placeholder="Select Vendor.." autocomplete="off" value={name}/>
                            <ul class="dropdown-menu w-100 vendors-available position-absolute" id="vnd_drop"  style={{overflowY:'auto',height:'fit-content',maxHeight:'40vh'}}> 
                                    <li class="dropdown-item vendors-options" onclick="getVendorDetails('','')">Select Vendor</li>
                                    {vendors && vendors.map((vnd) => (
                                    <li class="dropdown-item vendors-options" onClick={() => getVendorDetails(vnd.id)} >{ vnd.Title } { vnd.First_name } { vnd.Last_name }</li>
                                  ))}
                                </ul>
                                    {/* <select className="form-control">
                                    <option value="" selected> Select Vendor</option>
                                    {vendors && vendors.map((vnd) => (
                                      <option value={vnd.id} onChange={() => getVendorDetails(vnd.id)}>{vnd.Title} {vnd.First_name} {vnd.Last_name}</option>
                                    ))}
                                    </select> */}
                               
                                
                            </div>
                        </div>
                        <button type="button" data-toggle="modal" data-target="#newVendor" className="btn btn-outline-secondary ml-1" style={{width:'50px',height:'38px',position:'relative',bottom:'10px'}}>+</button>
                    </div>

                    <label className="mt-3">GST Type</label>
                    <input type="text" className="form-control" id="vendorGstType" name="vendor_gst_type" placeholder="GST Treatment" style={{backgroundColor:'#43596c'}} readonly value={gst_type}/>
                </div>

                <div className="col-md-4 mt-3">
                    <label className="">Email</label>
                    <input className="form-control" type="email" name="vendorEmail" placeholder="Email" style = {{backgroundColor:'#43596c',color:'white'}} id="vendorEmail" readonly value={email}/>
                    <div className="mt-3">
                        <input hidden value="{{cmp.State}}" id="cmpstate" />
                        <label className="">Source of supply</label>
                        <select type="text" className="form-control" id="sourceOfSupply" name="source_of_supply" style = {{backgroundColor:'#43596c',color:'white'}} required value={place_of_supply}>
                            <option value="" selected>--Choose--</option>
                            <option value="Andaman and Nicobar Islads">Andaman and Nicobar Islads</option>
                            <option value="Andhra Predhesh">Andhra Predhesh</option>
                            <option value="Arunachal Predesh">Arunachal Predesh</option>
                            <option value="Assam">Assam</option>
                            <option value="Bihar">Bihar</option>
                            <option value="Chandigarh">Chandigarh</option>
                            <option value="Chhattisgarh">Chhattisgarh</option>
                            <option value="Dadra and Nagar Haveli">Dadra and Nagar Haveli</option>
                            <option value="Damn anad Diu">Damn anad Diu</option>
                            <option value="Delhi">Delhi</option>
                            <option value="Goa">Goa</option>
                            <option value="Gujarat">Gujarat</option>
                            <option value="Haryana">Haryana</option>
                            <option value="Himachal Predesh">Himachal Predesh</option>
                            <option value="Jammu and Kashmir">Jammu and Kashmir</option>
                            <option value="Jharkhand">Jharkhand</option>
                            <option value="Karnataka">Karnataka</option>
                            <option value="Kerala">Kerala</option>
                            <option value="Ladakh">Ladakh</option>
                            <option value="Lakshadweep">Lakshadweep</option>
                            <option value="Madhya Predesh">Madhya Predesh</option>
                            <option value="Maharashtra">Maharashtra</option>
                            <option value="Manipur">Manipur</option>
                            <option value="Meghalaya">Meghalaya</option>
                            <option value="Mizoram">Mizoram</option>
                            <option value="Nagaland">Nagaland</option>
                            <option value="Odisha">Odisha</option>
                            <option value="Puducherry">Puducherry</option>
                            <option value="Punjab">Punjab</option>
                            <option value="Rajasthan">Rajasthan</option>
                            <option value="Sikkim">Sikkim</option>
                            <option value="Tamil Nadu">Tamil Nadu</option>
                            <option value="Telangana">Telangana</option>
                            <option value="Tripura">Tripura</option>
                            <option value="Uttar Predesh">Uttar Predesh</option>
                            <option value="Uttarakhand">Uttarakhand</option>
                            <option value="West Bengal">West Bengal</option>
                            <option value="Other Territory">Other Territory</option>
                        </select>
                    </div>
                </div>

                <div className="col-md-4 mt-3">
                    <label className="">Billing Address</label>
                    <textarea className="form-control" name="vendor_bill_address" id="vendorBillAddress" rows="4" style = {{backgroundColor:'#43596c',color:'white'}} readonly value={address}></textarea>
                </div>

                <div className="col-md-4 mt-3">
                    <div className="" id="vendorGstInDisplay" style={{display:'block'}}>
                        <label className="">GSTIN</label>
                        <input type="text" className="form-control" id="vendorGstin" name="vendor_gstin" placeholder="GSTIN" style={{backgroundColor:'#43596c'}} readonly value={gstIN}/>
                    </div>
                </div>
            </div>

            <div className="card-title mt-4">
                <h4 className="mb-0">Purchase Order Details</h4>
            </div>
            <hr/>

            <div className="row">
                <div className="col-md-4 mt-3">
                    <div className="d-flex">
                        <label className="">Purchase Order No.</label><span className="text-danger ml-3" id="PONoErr"></span>
                    </div>
                    <input type="text" className="form-control" name="purchase_order_no"  id="purchaseOrderNumber" style={{backgroundColor:'#43596c'}} placeholder="PONo" required />
                </div>
                <div className="col-md-4 mt-3">
                    <label className="">Reference Number</label>
                    <input type="text" className="form-control" name="reference_number" value="{{ref_no}}" style={{backgroundColor:'#43596c'}} readonly />
                </div>
                <div className="col-md-4 mt-3">
                    <label className="">Purchase Order Date:</label>
                    <input type="date" className="form-control" name="purchase_order_date" id="purchaseOrderDate" style = {{backgroundColor:'#43596c',color:'white'}}  />
                    {/* value="{% now 'Y-m-d' %}" */}
                </div>
                <div className="col-md-4 mt-3">
                    <label className="">Due Date:</label>
                    <input type="text" id="dueDate" className="form-control" name="due_date" style = {{backgroundColor:'#43596c',color:'white'}} readonly />
                </div>
                <div className="col-md-4 mt-3">
                    <label className="">Payment Terms </label>
                    <div className="d-flex">
                        <select className="form-control" name="payment_term" style = {{backgroundColor:'#43596c',color:'white'}} id="paymentTerm" required>
                            <option value="" selected> Select Payment Term</option>
                            {terms &&
                          terms.map((term) => (
                            <option value={term.id} text={term.days}>
                              {term.term_name}
                            </option>
                          ))}
                        </select>
                        <a className="btn btn-outline-secondary ml-1" role="button" data-target="#newPaymentTerm" data-toggle="modal" id="termsadd" style={{width:'50px',height:'38px',position:'relative',bottom:'10px'}}>+</a>
                    </div>
                </div>

                <div className="col-md-4 mt-3">
                    <label className="">Payment Type</label>
                    <select className="form-control my-select" id="paymentMethod" name="payment_method" style={{backgroundColor:'#43596c'}}>
                        <option value="" selected>Select Payment Method</option>
                        <option value="Cash">Cash</option>
                        <option value="Cheque">Cheque</option>
                        <option value="UPI">UPI</option>
                        {/* {% for b in banks %}
                        <option value="{{ b.bank_name }}" text="{{ b.id }}">{{ b.bank_name }} (XXX{{ b.account_number|slice:"-4:" }})</option>
                        {% endfor %} */}
                    </select>
                </div>
                <div className="col-md-4 mt-3" style={{display:'none'}}  id="chequediv">
                    <label className="" >Cheque No</label>
                    <input type="text" className="form-control" name="cheque_id" id="cheque_id" placeholder="Enter Cheque No" />
                </div>
                <div className="col-md-4 mt-3"  style={{display:'none'}} id="upidiv">
                    <label className="" >UPI ID</label>
                    <input type="text" className="form-control" name="upi_id" id="upi_id" placeholder="Enter UPI ID" />
                </div>
                <div className="col-md-4 mt-3"  style={{display:'none'}} id="bnkdiv">
                    <label className="" >Account#</label>
                    <input type="text" className="form-control" name="bnk_id" id="bnk_id" style={{backgroundColor:'#43596c'}} readonly />
                </div>
            </div>

            <div className="card-title mt-4">
                <h4 className="mb-0">Deliver To Details</h4>
            </div>
            <hr/>

            <div className="row">
                <div className="col-md-4 mt-3">
                    <label className="">Select Customer</label><span className="text-danger ml-3" id="custErr"></span>
                    <input type="hidden" name="customerId" id="customerId" value="" />
                    <div className="d-flex">
                        <div className="w-100">
                            <div className="p-0 border-0 bg-none position-relative drop-box" style={{display:'block'}}>
                                <input required type="text" id="customer" value={cname} name="customer" className="dropdown-toggle form-control customers-display" onkeyup="filterCustomers()" data-toggle="dropdown" aria-expanded="false" placeholder="Select Customer.." autocomplete="off" />
                                <ul className="dropdown-menu w-100 customers-available position-absolute" id="cust_drop"  style={{overflowY:'auto',height:'fit-content',maxHeight:'40vh'}}> 
                                    <li className="dropdown-item customers-options" onclick="getCustomerDetails('','')">Select Customer</li>
                                    {/* {% for cust in customers %}
                                    <li className="dropdown-item customers-options" onclick="getCustomerDetails(`{{cust.id}}`,this.innerHTML)">{{ cust.title }} {{ cust.first_name }} {{ cust.last_name }}</li>
                                    {% endfor %} */}
                                    {customers && customers.map((cust) =>(
                                      <li className="dropdown-item customers-options" onClick={() =>get_customer_details(cust.id)}>{ cust.title } { cust.first_name } { cust.last_name }</li>
                                    ))}
                                </ul>
                                
                            </div>
                        </div>
                        <button type="button" data-toggle="modal" data-target="#newCustomer" className="btn btn-outline-secondary ml-1" style={{width:'50px',height:'38px',position:'relative',bottom:'10px'}}>+</button>
                    </div>

                    <label className="mt-3">GST Type</label>
                    <input type="text" className="form-control" id="gstType" name="gst_type" placeholder="GST Treatment" style={{backgroundColor:'#43596c'}} readonly value={cgst_type}/>
                </div>

                <div className="col-md-4 mt-3">
                    <label className="">Email</label>
                    <input className="form-control" type="email" name="customerEmail" placeholder="Email" style = {{backgroundColor:'#43596c',color:'white'}} id="customerEmail" readonly value={cemail}/>
                    <div className="mt-3">
                        <label className="">Place of supply</label>
                        <select type="text" className="form-control" id="placeOfSupply" name="place_of_supply" style = {{backgroundColor:'#43596c',color:'white'}} required value={cplace_of_supply}>
                            <option value="" selected>--Choose--</option>
                            <option value="Andaman and Nicobar Islads">Andaman and Nicobar Islads</option>
                            <option value="Andhra Predhesh">Andhra Predhesh</option>
                            <option value="Arunachal Predesh">Arunachal Predesh</option>
                            <option value="Assam">Assam</option>
                            <option value="Bihar">Bihar</option>
                            <option value="Chandigarh">Chandigarh</option>
                            <option value="Chhattisgarh">Chhattisgarh</option>
                            <option value="Dadra and Nagar Haveli">Dadra and Nagar Haveli</option>
                            <option value="Damn anad Diu">Damn anad Diu</option>
                            <option value="Delhi">Delhi</option>
                            <option value="Goa">Goa</option>
                            <option value="Gujarat">Gujarat</option>
                            <option value="Haryana">Haryana</option>
                            <option value="Himachal Predesh">Himachal Predesh</option>
                            <option value="Jammu and Kashmir">Jammu and Kashmir</option>
                            <option value="Jharkhand">Jharkhand</option>
                            <option value="Karnataka">Karnataka</option>
                            <option value="Kerala">Kerala</option>
                            <option value="Ladakh">Ladakh</option>
                            <option value="Lakshadweep">Lakshadweep</option>
                            <option value="Madhya Predesh">Madhya Predesh</option>
                            <option value="Maharashtra">Maharashtra</option>
                            <option value="Manipur">Manipur</option>
                            <option value="Meghalaya">Meghalaya</option>
                            <option value="Mizoram">Mizoram</option>
                            <option value="Nagaland">Nagaland</option>
                            <option value="Odisha">Odisha</option>
                            <option value="Puducherry">Puducherry</option>
                            <option value="Punjab">Punjab</option>
                            <option value="Rajasthan">Rajasthan</option>
                            <option value="Sikkim">Sikkim</option>
                            <option value="Tamil Nadu">Tamil Nadu</option>
                            <option value="Telangana">Telangana</option>
                            <option value="Tripura">Tripura</option>
                            <option value="Uttar Predesh">Uttar Predesh</option>
                            <option value="Uttarakhand">Uttarakhand</option>
                            <option value="West Bengal">West Bengal</option>
                            <option value="Other Territory">Other Territory</option>
                        </select>
                    </div>
                </div>

                <div className="col-md-4 mt-3">
                    <label className="">Billing Address</label>
                    <textarea className="form-control" name="bill_address" id="billAddress" rows="4" style = {{backgroundColor:'#43596c',color:'white'}} readonly value={caddress}></textarea>
                </div>
                <div className="col-md-4 mt-3">
                    <div id="gstInDisplay" style={{display:'block'}}>
                        <label className="">GSTIN</label>
                        <input type="text" className="form-control" id="gstin" name="gstin" placeholder="GSTIN" style={{backgroundColor:'#43596c'}} readonly value={cgstIN}/>
                    </div>
                </div>
            </div>

            <div className="row" id="applyPriceListSection" style={{display:'block'}}>
                <div className="col-md-3 mt-3">
                    <div className="form-group form-check">
                        <input type="checkbox" className="form-check-input" name="priceList" id="applyPriceList" value="applyPriceList" />
                        <input type="hidden" name="priceListId" value="" id="customerPriceListId" />
                        <label className="form-check-label" for="applyPriceList">Apply Price List</label>
                        <span className="text-success" id="custPriceListName" style={{display:'none',marginLeft:'5px'}}></span>
                    </div>
                    <div id="priceListDropdown" style={{display:'none'}}>
                        <label className="">Price List</label>
                        <span className="text-danger" id="custPriceListAlert" style={{display:'none',marginLeft:'5px'}}></span>
                        <select className="form-control" id="priceListIds" name="price_list_id" style={{backgroundColor:'#43596c'}}>
                            <option value="">Choose Price List</option>
                            {/* {% for p in priceListItems %}
                            <option value="{{p.id}}">{{p.name}}</option>
                            {% endfor %} */}
                        </select>
                    </div>
                </div>

                <div className="col-md-3 mt-3">
                    
                </div>
            </div>

            <div className="row clearfix ">
                  <div className="col-md-12 table-responsive-md mt-3">
                    <table
                      className="table table-bordered table-hover mt-3"
                      id="salesOrderItemsTable"
                    >
                      <thead>
                        <tr>
                          <th className="text-center">#</th>
                          <th className="text-center">PRODUCT / SERVICE</th>
                          <th className="text-center">HSN / SAC</th>
                          <th className="text-center">QTY</th>
                          <th className="text-center">PRICE</th>
                          <th className="text-center">TAX (%)</th>
                          <th className="text-center">DISCOUNT</th>
                          <th className="text-center">TOTAL</th>
                        </tr>
                      </thead>
                      <tbody id="items-table-body">
                        {items && items.map((row) => (
                          <tr  key={row.id}>         
                          
                            <td
                              className="nnum"
                              style={{ textAlign: "center" }}
                              id={`tab_row${row.id}`}
                            >
                              {row.id}
                            </td>
                            <td style={{ width: "20%" }}>
                              <div className="d-flex align-items-center">
                                <Select
                                  // options={items}
                                  styles={customStyles}
                                  name="item"
                                  className="w-100"
                                  // id={`item${row.id}`}
                                  required
                                  value={row.name}
                                  // defaultInputValue={row.name}
                                //   onChange={(selectedOption) =>
                                //     handleItemChange(
                                //       selectedOption
                                //         ? selectedOption.value
                                //         : "",
                                //       row.id
                                //     )
                                //   }
                                //   onBlur={refreshValues}
                                  isClearable
                                  isSearchable
                                />
                                <button
                                  type="button"
                                  className="btn btn-outline-secondary ml-1"
                                  data-target="#newItem"
                                  data-toggle="modal"
                                  style={{
                                    width: "fit-content",
                                    height: "fit-content",
                                  }}
                                >
                                  +
                                </button>
                              </div>
                            </td>
                            <td>
                              <input
                                type="text"
                                name="hsnSac"
                                value={row.hsnSac}
                                // id={`hsn${row.id}`}
                                placeholder="HSN/SAC Code"
                                className="form-control HSNCODE"
                                style={{
                                  backgroundColor: "#43596c",
                                  color: "white",
                                }}
                                readOnly
                              />
                            </td>
                            <td>
                              <input
                                type="number"
                                name="qty[]"
                                // id={`qty${row.id}`}
                                className="form-control qty"
                                step="0"
                                min="1"
                                style={{
                                  backgroundColor: "#43596c",
                                  color: "white",
                                }}
                                value={row.quantity}
                                // onChange={(e) =>
                                //   handleSalesOrderItemsInputChange(
                                //     row.id,
                                //     "quantity",
                                //     e.target.value
                                //   )
                                // }
                                // onBlur={refreshValues}
                                required
                              />
                            </td>
                            <td>
                              <input
                                type="number"
                                name="price"
                                // id={`price${row.id}`}
                                className="form-control price"
                                step="0.00"
                                min="0"
                                style={{
                                  backgroundColor: "#43596c",
                                  color: "white",
                                  display: "block",
                                }}
                                value={row.price}
                                readOnly
                              />
                              <input
                                type="number"
                                name="priceListPrice"
                                // id={`priceListPrice${row.id}`}
                                className="form-control priceListPrice"
                                step="0.00"
                                min="0"
                                style={{
                                  backgroundColor: "#43596c",
                                  color: "white",
                                  display: "none",
                                }}
                                value={row.priceListPrice}
                                readOnly
                              />
                            </td>

                            <td style={{ width: "13%" }}>
                              <select
                                name="taxGST"
                                // id={`taxGST${row.id}`}
                                className="form-control tax_ref tax_ref_gst"
                                style={{ display: "block" }}
                                value={row.taxGst}
                                // onChange={(e) =>
                                //   handleSalesOrderItemsInputChange(
                                //     row.id,
                                //     "taxGst",
                                //     e.target.value
                                //   )
                                // }
                                // onBlur={refreshValues}
                              >
                                <option value="">Select GST</option>
                                <option value="28">28.0% GST</option>
                                <option value="18">18.0% GST</option>
                                <option value="12">12.0% GST</option>
                                <option value="5">05.0% GST</option>
                                <option value="3">03.0% GST</option>
                                <option value="0">0.0% GST</option>
                              </select>
                              <select
                                name="taxIGST"
                                // id={`taxIGST${row.id}`}
                                className="form-control tax_ref tax_ref_igst"
                                style={{ display: "none" }}
                                value={row.taxIgst}
                                // onChange={(e) =>
                                //   handleSalesOrderItemsInputChange(
                                //     row.id,
                                //     "taxIgst",
                                //     e.target.value
                                //   )
                                // }
                                // onBlur={refreshValues}
                              >
                                <option value="">Select IGST</option>
                                <option value="28">28.0% IGST</option>
                                <option value="18">18.0% IGST</option>
                                <option value="12">12.0% IGST</option>
                                <option value="5">05.0% IGST</option>
                                <option value="3">03.0% IGST</option>
                                <option value="0">0.0% IGST</option>
                              </select>
                            </td>
                            <td>
                              <input
                                type="number"
                                name="discount"
                                placeholder="Enter Discount"
                                // id={`disc${row.id}`}
                                value={row.discount}
                                // onChange={(e) =>
                                //   handleSalesOrderItemsInputChange(
                                //     row.id,
                                //     "discount",
                                //     e.target.value
                                //   )
                                // }
                                // onBlur={refreshValues}
                                className="form-control disc"
                                step="0"
                                min="0"
                                style={{
                                  backgroundColor: "#43596c",
                                  color: "white",
                                }}
                              />
                            </td>

                            <td>
                              <input
                                type="number"
                                name="total"
                                // id={`total${row.id}`}
                                className="form-control total"
                                value={row.total}
                                readOnly
                                style={{
                                  backgroundColor: "#43596c",
                                  color: "white",
                                }}
                              />
                              <input
                                type="hidden"
                                // id={`taxamount${row.id}`}
                                className="form-control itemTaxAmount"
                                value={row.taxAmount}
                              />
                            </td>
                            <td>
                              <button
                                type="button"
                                // id={`${row.id}`}
                                style={{
                                  width: "fit-content",
                                  height: "fit-content",
                                }}
                                // onClick={() => removeRow(row.id)}
                                className="btn btn-danger remove_row px-2 py-1 mx-1 fa fa-close"
                                title="Remove Row"
                              ></button>
                            </td>
                          </tr>
                        ))} 
                      </tbody>
                      <tr>
                        <td style={{ border: "none" }}>
                          <a
                            className="btn btn-secondary ml-1"
                            role="button"
                            id="add"
                            // onClick={addNewRow}
                            style={{
                              width: "fit-content",
                              height: "fit-content",
                            }}
                          >
                            +
                          </a>
                        </td>
                      </tr>
                    </table>
                  </div>
                </div>
            <div className="row clearfix" style={{marginTop:'20px'}}>
                <div className="col-md-6">
                    <textarea className="form-control mt-3"  id="" name="note" placeholder="Note" style={{height:'190px'}}></textarea>
                    <input type="file" name="file"  style={{marginTop:'20px',width:'70%'}} />
                </div>            
                <div className="col-md-1"></div>
                <div className="col-md-5 table-responsive-md mt-3 " id="purchaseOrderItemsTableTotal" style={{backgroundColor:'rgba(0,0,0,.4)',border:' 1px solid rgba(128, 128, 128, 0.6)',marginLeft:'-2vh'}}>
                    <div className="p-3">
                        <div className="row container-fluid p-2 m-0">
                            <div className="col-sm-4 mt-2"><label className="text-center">Sub Total</label></div>
                            <div className="col-sm-1 mt-2">:</div>
                            <div className="col-sm-7 mt-2"><input type="number" step="any" name='subtotal' value={0.00} readonly style={{backgroundColor:'#37444f'}} className="form-control" id="sub_total" /></div>
                        </div>
                        <div className="row container-fluid p-2 m-0" id="taxamountIGST" style={{display:'flex'}}>
                            <div className="col-sm-4 mt-2"><label for="a" className="text-center">IGST</label></div>
                            <div className="col-sm-1 mt-2">:</div>
                            <div className="col-sm-7 mt-2"><input type="number" name='igst' step="any" id="igstAmount" value={0.00} readonly style={{backgroundColor:'#37444f'}} className="form-control"/></div>
                        </div>
                        <div className="row container-fluid p-2 m-0" style={{display:'none'}} id="taxamountCGST">
                            <div className="col-sm-4 mt-2"><label for="a" className="text-center">CGST</label></div>
                            <div className="col-sm-1 mt-2">:</div>
                            <div className="col-sm-7 mt-2"><input type="number" name='cgst' step="any" id="cgstAmount" value={0.00} readonly style={{backgroundColor:'#37444f'}} className="form-control"/></div>
                        </div>
                        <div className="row container-fluid p-2 m-0" style={{display:'none'}} id="taxamountSGST">
                            <div className="col-sm-4 mt-2"><label for="a" className="text-center">SGST</label></div>
                            <div className="col-sm-1 mt-2">:</div>
                            <div className="col-sm-7 mt-2"><input type="number" name='sgst' step="any" id="sgstAmount" value={0.00} readonly style={{backgroundColor:'#37444f'}} className="form-control"/></div>
                        </div>
                        <div className="row container-fluid p-2 m-0">
                            <div className="col-sm-4 mt-2"><label for="a" className="text-center">Tax Amount</label></div>
                            <div className="col-sm-1 mt-2">:</div>
                            <div className="col-sm-7 mt-2"><input type="number" step="any" name='taxamount' id="tax_amount" value={0.00} readonly style={{backgroundColor:'#37444f'}} className="form-control"/></div>
                        </div>
                        
                        <div className="row container-fluid p-2 m-0">
                            <div className="col-sm-4 mt-2"><label for="a" className="text-center">Shipping Charge</label></div>
                            <div className="col-sm-1 mt-2">:</div>
                            <div className="col-sm-7 mt-2"><input type="number" step="any" name='ship' id="ship" value={0.00} className="form-control"/></div>
                        </div>
                        <div className="row container-fluid p-2 m-0">
                            <div className="col-sm-4 mt-2"><label for="a" className="text-center">Adjustment</label></div>
                            <div className="col-sm-1 mt-2">:</div>
                            <div className="col-sm-7 mt-2"><input type="number" step="any" name='adj' id="adj" value={0.00} className="form-control"/></div>
                        </div>
                        <div className="row container-fluid p-2 m-0">
                            <div className="col-sm-4 mt-2"><label for="a" className="text-center">Grand Total</label></div>
                            <div className="col-sm-1 mt-2">:</div>
                            <div className="col-sm-7 mt-2"><input type="number" name='grandtotal' id="grandtotal" value={0.00} readonly style={{backgroundColor:'#37444f'}} className="form-control"/></div>
                        </div>
                    </div>
                </div>
            </div>
            <div className="row">
                <div className="col-md-7"></div>
                <div className="col-md-5 table-responsive-md mt-3 " id="purchaseOrderItemsTablePaid" style={{backgroundColor:'rgba(0,0,0,.4)',border:'1px solid rgba(128, 128, 128, 0.6)',marginLeft:'-2vh'}}>
                    <div className="p-3">
                        <div className="row container-fluid p-2 m-0">
                            <div className="col-sm-4 mt-2"><label for="a" className="text-center">Paid Off</label></div>
                            <div className="col-sm-1 mt-2">:</div>
                            <div className="col-sm-7 mt-2"><input type="number" step="any" name='advance' id="advance"  value={0.00} className="form-control"/></div>
                        </div>
                        <div className="row container-fluid p-2 m-0">
                            <div className="col-sm-4 mt-2"><label for="a" className="text-center">Balance</label></div>
                            <div className="col-sm-1 mt-2">:</div>
                            <div className="col-sm-7 mt-2"><input type="number" name='balance' id="balance" value={0.00} readonly style={{backgroundColor:'#37444f'}} className="form-control" /></div>
                        </div>
                    </div>
                </div>
            </div>

        
            <div className="row">
                <div className="col-md-7 mt-3">
                    <div className="form-check">
                        <input className="form-check-input" type="checkbox" value="" id="agreeTerms" required style={{backgroundColor:'#43596c'}} />
                        <label for="agreeTerms">Agree to terms and conditions</label>
                        <div className="invalid-feedback">You must agree before submitting.</div>
                    </div>
                </div>
                <div className="col-md-5 mt-3 d-flex">
                    <input type="submit" className="btn btn-outline-secondary w-50 text-light" name="Draft" value="Draft" />
                    <input type="submit" className="btn btn-outline-secondary w-50 ml-1 text-light" name="Save" value="Save" />
                </div>
            </div>
            <div className="notices mt-3">
                <div className="text-muted">NOTICE:</div>
                <div className="text-muted">Fin sYs Terms and Conditions Apply</div>
            </div>
            <footer className="text-muted">Purchase Order was created on a computer and is valid without the signature and seal.</footer>
        </div>
      </div>
    </div>
  </div>
</form>



        </>
    )
}
export default Add_Purchase_Order;