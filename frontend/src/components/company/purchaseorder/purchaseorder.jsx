import React, { useEffect, useState } from "react";
import FinBase from "../FinBase";
import * as XLSX from "xlsx";
import { Link, useNavigate } from "react-router-dom";
import Cookies from 'js-cookie';
import axios from "axios";
import config from "../../../functions/config";


function Purchase_order () {




    return (
        <>
        <FinBase />
        <div
        className="page-content"
        style={{ backgroundColor: "#2f516f", minHeight: "100vh" }}
      >
        <div className="card radius-15 h-20">
          <div className="row">
            <div className="col-md-12">
              <center>
                <h2 className="mt-3">PURCHASE ORDERS</h2>
              </center>
              <hr />
            </div>
          </div>
        </div>

        <div className="card radius-15">
          <div className="card-body">
            <div className="container-fluid">
              <div className="row">
                <div className="col-md-4">
                  <div className="d-flex align-items-center">
                    <input
                      type="text"
                      id="search"
                      className="form-control"
                      placeholder="Search.."
                      autoComplete="off"
                    //   onKeyUp={searchTable}
                    />
                    <div
                      className="dropdown ml-1"
                      style={{ justifyContent: "left" }}
                    >
                      <button
                        type="button"
                        style={{ width: "fit-content", height: "fit-content" }}
                        className="btn btn-outline-secondary dropdown-toggle text-grey"
                        data-toggle="dropdown"
                      >
                        <i className="fa fa-sort"></i> Sort by
                      </button>
                      <div
                        className="dropdown-menu"
                        style={{ backgroundColor: "black" }}
                      >
                        <a
                          className="dropdown-item"
                        //   onClick={refreshAll}
                          style={{
                            height: "40px",
                            fontSize: "15px",
                            color: "white",
                          }}
                        >
                          All
                        </a>
                        <a
                          className="dropdown-item"
                          style={{
                            height: "40px",
                            fontSize: "15px",
                            color: "white",
                            cursor: "pointer",
                          }}
                        //   onClick={()=>sortTable(2)}
                        >
                          Customer Name
                        </a>
                        <a
                          className="dropdown-item"
                          style={{
                            height: "40px",
                            fontSize: "15px",
                            color: "white",
                            cursor: "pointer",
                          }}
                        //   onClick={()=>sortTable(1)}
                        >
                          Sales Order No.
                        </a>
                      </div>
                    </div>
                  </div>
                </div>
                <div className="col-md-2"></div>
                <div className="col-md-6 d-flex justify-content-end">
                  <button
                    type="button"
                    style={{ width: "fit-content", height: "fit-content" }}
                    className="btn btn-outline-secondary text-grey"
                    id="exportBtn"
                    // onClick={exportToExcel}
                  >
                    <i className="fa fa-table"></i> Export To Excel
                  </button>
                  <div className="dropdown ml-1">
                    <button
                      type="button"
                      style={{ width: "fit-content", height: "fit-content" }}
                      className="btn btn-outline-secondary dropdown-toggle text-grey"
                      data-toggle="dropdown"
                    >
                      <i className="fa fa-filter"></i> filter by
                    </button>
                    <div
                      className="dropdown-menu"
                      style={{ backgroundColor: "black" }}
                    >
                      <a
                        className="dropdown-item"
                        style={{
                          height: "40px",
                          fontSize: "15px",
                          color: "white",
                          cursor: "pointer",
                        }}
                        // onClick={()=>filterTable(5,'all')}
                      >
                        All
                      </a>
                      <a
                        className="dropdown-item"
                        style={{
                          height: "40px",
                          fontSize: "15px",
                          color: "white",
                          cursor: "pointer",
                        }}
                        // onClick={()=>filterTable(5,'saved')}
                      >
                        Saved
                      </a>
                      <a
                        className="dropdown-item"
                        style={{
                          height: "40px",
                          fontSize: "15px",
                          color: "white",
                          cursor: "pointer",
                        }}
                        // onClick={()=>filterTable(5,'draft')}
                      >
                        Draft
                      </a>
                    </div>
                  </div>
                  <Link to="/add_purchase_order" className="ml-1">
                    <button
                      type="button"
                      style={{ width: "fit-content", height: "fit-content" }}
                      className="btn btn-outline-secondary text-grey"
                    >
                      <i className="fa fa-plus font-weight-light"></i> Purchase Order
                    </button>
                  </Link>
                </div>
              </div>
            </div>
          </div>
          <div className="table-responsive">
            <table
              className="table table-responsive-md table-hover mt-4"
              id="salesOrderTable"
              style={{ textAlign: "center" }}
            >
              <thead>
                <tr>
                <th>#</th>
                <th>DATE</th>
                <th>PURCHASE ORDER NO.</th>
                <th>VENDOR NAME</th>
                <th>MAIL ID</th>
                <th>AMOUNT</th>
                <th>STATUS</th>
                <th>BALANCE</th>
                <th>ACTION</th>
                </tr>
              </thead>
              <tbody>
                {/* {salesOrders &&salesOrders.map((i,index)=>(
                  <tr
                    className="clickable-row"
                    onDoubleClick={()=>navigate(`/view_sales_order/${i.id}/`)}
                    style={{ cursor: "pointer" }}
                  >
                    <td>{index+1}</td>
                    <td>{i.sales_order_no}</td>
                    <td>{i.customer_name}</td>
                    <td>{i.customer_email}</td>
                    <td>{i.grandtotal}</td>
                    <td>{i.status}</td>
                    <td>{i.balance}</td>
                    <td>
                      <div className="btn-group">
                        <button type="button" className="btn btn-secondary dropdown-toggle" style={{width:'fit-content', height: 'fit-content'}} data-toggle="dropdown" aria-expanded="false">
                            Convert
                        </button>
                        <ul className="dropdown-menu">
                          <li><button type="button" className="dropdown-item fw-bold" onclick="window.location.href=`{% url 'Fin_convertSalesOrderToInvoice' a.id %}`">To Invoice</button></li>
                          <li><button type="button" className="dropdown-item fw-bold" onclick="window.location.href=`{% url 'Fin_convertSalesOrderToRecInvoice' a.id %}`">To Recurring Invoice</button></li>
                        </ul>
                      </div>
                    </td>
                  </tr>
                ))} */}
              </tbody>
            </table>
          </div>
        </div>
      </div>
      <table className="salesOrderTable" id="salesOrderTableExport" hidden>
      <thead>
        <tr>
          <th>#</th>
          <th>DATE</th>
          <th>PURCHASE ORDER NO.</th>
          <th>VENDOR NAME</th>
          <th>MAIL ID</th>
          <th>AMOUNT</th>
          <th>STATUS</th>
          <th>BALANCE</th>
        </tr>
      </thead>
      <tbody>
        {/* {salesOrders && salesOrders.map((i,index)=>(
          <tr>
            <td>{index+1}</td>
            <td>{i.sales_order_no}</td>
            <td>{i.customer_name}</td>
            <td>{i.customer_email}</td>
            <td>{i.grandtotal}</td>
            <td>{i.status}</td>
            <td>{i.balance}</td>
          </tr>
        ))} */}
      </tbody>
      </table>
        </>
    )

}
export default Purchase_order;