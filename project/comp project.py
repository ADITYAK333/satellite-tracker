import tkinter as tk
from tkinter import messagebox
import mysql.connector



# Function to connect to MySQL database
def connect_to_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",  # Replace with your MySQL username
        password="root",  # Replace with your MySQL password
        database="aditya"
    )

# Function to add a new property
def add_property():
    name, loc, price, size = entry_name.get(), entry_location.get(), entry_price.get(), entry_size.get()
    
    if not (name and loc and price and size):  # Check if fields are empty
        messagebox.showwarning("Error", "All fields must be filled")
        return

    try:
        conn = connect_to_db()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO properties (property_name, location, price, size) VALUES (%s, %s, %s, %s)", 
                       (name, loc, price, size))
        conn.commit()
        messagebox.showinfo("Success", "Property added successfully")
        display_properties()
    finally:
        conn.close()

# Function to display all properties
def display_properties():
    conn = connect_to_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM properties")
    listbox.delete(0, tk.END)
    for row in cursor.fetchall():
        listbox.insert(tk.END, f"{row[0]}: {row[1]} | {row[2]} | ${row[3]} | {row[4]} sq ft")
    conn.close()

# Function to delete a selected property
def delete_property():
    selected = listbox.curselection()
    if not selected:
        messagebox.showwarning("Error", "No property selected")
        return
    
    prop_id = listbox.get(selected).split(":")[0]  # Get the ID of selected property
    
    conn = connect_to_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM properties WHERE id = %s", (prop_id,))
    conn.commit()
    conn.close()
    display_properties()

# Setting up the Tkinter window
root = tk.Tk()
root.title("Real Estate Management")

# Input fields and labels
tk.Label(root, text="Property Name").grid(row=0, column=0)
entry_name = tk.Entry(root)
entry_name.grid(row=0, column=1)

tk.Label(root, text="Location").grid(row=1, column=0)
entry_location = tk.Entry(root)
entry_location.grid(row=1, column=1)

tk.Label(root, text="Price").grid(row=2, column=0)
entry_price = tk.Entry(root)
entry_price.grid(row=2, column=1)

tk.Label(root, text="Size (sq ft)").grid(row=3, column=0)
entry_size = tk.Entry(root)
entry_size.grid(row=3, column=1)

# Buttons
tk.Button(root, text="Add Property", command=add_property).grid(row=4, column=0, columnspan=2)
tk.Button(root, text="Delete Property", command=delete_property).grid(row=5, column=0, columnspan=2)

# Listbox to display properties
listbox = tk.Listbox(root, width=50)
listbox.grid(row=6, column=0, columnspan=2)

# Display all properties on startup
display_properties()

# Run the Tkinter application
root.mainloop()
