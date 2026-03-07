import sqlite3

def add_styles():
    print("Add styles to the database")
    style_size = input("Enter the style size: ")
    mct1 = input("Enter the capacity number of MCT1: ")
    mct2 = input("Enter the capacity number of MCT2: ")
    mct3 = input("Enter the capacity number of MCT3: ")
    mct4 = input("Enter the capacity number of MCT4: ")
    mct5 = input("Enter the capacity number of MCT5: ")
    mct6 = input("Enter the capacity number of MCT6: ")
    mct7 = input("Enter the capacity number of MCT7: ")
    mct8 = input("Enter the capacity number of MCT8: ")
    mct9 = input("Enter the capacity number of MCT9: ")
    mct10 = input("Enter the capacity number of MCT10: ")
    mct11 = input("Enter the capacity number of MCT11: ")
    mct12 = input("Enter the capacity number of MCT12: ")
    July_demand = input("Enter the demand for July: ")


    conn = sqlite3.connect("production.db")
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO styles (style_size, mct1, mct2, mct3, mct4, mct5, mct6, mct7, mct8, mct9, mct10, mct11, mct12, July_demand)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (style_size, mct1, mct2, mct3, mct4, mct5, mct6, mct7, mct8, mct9, mct10, mct11, mct12, July_demand))
    conn.commit()
    print("Style added successfully")
    conn.close()


def remove_styles():
    print("Remove styles from the database")
    style_size = input("Enter the style size to remove: ").strip()
    conn = sqlite3.connect("production.db")
    cur = conn.cursor()
    cur.execute("DELETE FROM styles WHERE style_size = ?", (style_size,))
    conn.commit()
    print("Style removed successfully")
    conn.close()

def main_menu():
    while True:
        print("\n=============================")
        print("   Production DB Manager")
        print("=============================")
        print("  1. Add a style")
        print("  2. Remove a style")
        print("  3. Quit")
        print("=============================")

        choice = input("Choose an option (1/2/3): ").strip()

        if choice == "1":
            add_styles()
        elif choice == "2":
            remove_styles()
        elif choice == "3":
            print("Goodbye!")
            break
        else:
            print(" Invalid option, please enter 1, 2, or 3.")


if __name__ == "__main__":
    main_menu()
