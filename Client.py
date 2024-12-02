import sys
import tkinter as tk
from tkinter import messagebox, simpledialog
import xmlrpc.client
import threading
import time

lock = threading.Lock()

PORT = 8888
server = '127.0.0.1'
current_user = None
game_id = None  # 用來儲存當前遊戲 ID
FirOrSec = "player1"
root = tk.Tk()
colorarr = ["gray", "white", "black"]
buttons = [['0']*8 for _ in range(8)]
board = [['0', '0', '0', '0', '0', '0', '0', '0'],
         ['0', '0', '0', '0', '0', '0', '0', '0'],
         ['0', '0', '0', '0', '0', '0', '0', '0'],
         ['0', '0', '0', 'O', 'X', '0', '0', '0'],
         ['0', '0', '0', 'X', 'O', '0', '0', '0'],
         ['0', '0', '0', '0', '0', '0', '0', '0'],
         ['0', '0', '0', '0', '0', '0', '0', '0'],
         ['0', '0', '0', '0', '0', '0', '0', '0']]

a = tk.StringVar()
a.set("未登入")

def register_gui():
    global server
    name = simpledialog.askstring("註冊", "輸入使用者名稱：")
    password = simpledialog.askstring("註冊", "輸入密碼：")
    try:
        result = server.register(name, password)
        messagebox.showinfo("註冊", result)
    except Exception as e:
        messagebox.showerror("錯誤", f"註冊失敗: {e}")

def login_gui():
    global server, current_user
    name = simpledialog.askstring("登入", "輸入使用者名稱：")
    password = simpledialog.askstring("登入", "輸入密碼：")
    try:
        result = server.login(name, password)
        if "成功" in result:
            current_user = name
            a.set("玩家:" + current_user)
        messagebox.showinfo("登入", result + ":" + current_user)
    except Exception as e:
        messagebox.showerror("錯誤", f"登入失敗: {e}")

# 轮询棋盘更新
def poll_board_updates(game_id):
    global board
    while True:
        try:
            lock.acquire()
            #print(game_id)
            board_state = server.check_board_data(game_id)
            #print(board_state)
            if board_state:
                #print(board)
                lock.release()
                if board_state:
                    # Updating the board data based on the server response
                    for i in range(8):
                        for j in range(8):
                            board[i][j] = board_state[i*8+j]
                    # After the board is updated, we call the function to refresh the display
                    root.after(1, refresh_board)
                time.sleep(0.5)  # Sleep for 2 seconds to avoid excessive requests
            else:
                lock.release()
        except Exception as e:
            print(f"Polling failed: {e}")
            poll_board_updates(game_id)


# 刷新棋盘显示
def refresh_board():
    global board, buttons
    curr = server.get_curr_user(current_user,game_id)
    for row in range(8):
        for col in range(8):
            # Updating the button colors based on the current board state
            color = 'gray' if board[row][col] == '0' else 'white' if board[row][col] == 'O' else 'black' if board[row][col] == 'X' else 'red' if curr else 'gray'
            buttons[row][col].configure(bg=color)
    root.update()  # Refreshing the window display

def start_game_gui():
    global current_user, game_id,FirOrSec
    if not current_user:
        messagebox.showinfo("提示", "請先登入！")
        return
    print("偵錯點1")
    try:
        lock.acquire()
        result = server.start_game(current_user)  # Request to start the game
        lock.release()
        if current_user == result[2]:
            FirOrSec = "first"
        else:
            FirOrSec = "second"
        if "開始" in result:
            print("偵錯點2")
            game_id = result[0]
            # Starting a new window to display the game board
            new_window = tk.Toplevel()
            new_window.title("8x8 Chessboard")
            # Start the board polling in a separate thread
            threading.Thread(target=poll_board_updates, args=(game_id), daemon=True).start()
            display_board(new_window)  # Display the board in the new window
            messagebox.showinfo("遊戲狀態", result)
        elif "等待" in result:
            #messagebox.showinfo("提示", "等待對手加入遊戲...")
            time.sleep(2)
            start_game_gui()
    except Exception as e:
        messagebox.showerror("錯誤", f"遊戲開始失敗: {e}")


def display_board(new_window):
    global buttons, board
    board_frame = tk.Frame(new_window)
    board_frame.grid(row=0, column=0)
    user_info_frame = tk.Frame(new_window)
    user_info_frame.grid(row=1, column=0, pady=10)

    cell_size = 50  # 每個格子的大小
    buttons = [[None for _ in range(8)] for _ in range(8)]

    # 从服务器获取当前棋盘状态
    try:
        lock.acquire()
        result = server.check_board_data(game_id)
        lock.release()
        if result:
            # 更新 board 数据
            board = [list(result[i:i+8]) for i in range(0, len(result), 8)]
    except Exception as e:
        print(f"获取棋盘数据失败: {e}")
        messagebox.showerror("錯誤", "無法取得棋盤資料")
    name_label = tk.Label(user_info_frame, text="玩家1: " + current_user, width=10, height=3)
    name_label.grid(row=0, column=1)

    def on_button_click(row, col):
        make_move_gui(row, col,new_window)

    # 畫出棋盤格子
    for row in range(8):  
        for col in range(8):  
            button = tk.Button(board_frame, width=6, height=3, command=lambda r=row, c=col: on_button_click(r, c))
            button.grid(row=row, column=col, padx=2, pady=2)
            buttons[row][col] = button
    refresh_board()  # 更新棋盘显示


def make_move_gui(row, col,new_window):
    global current_user, game_id, board
    if not current_user:
        messagebox.showinfo("提示", "請先登入！")
        return
    try:
        lock.acquire()
        result = server.make_move(current_user, game_id, row, col)
        lock.release()
        messagebox.showinfo("遊戲狀態", result)

        # 更新棋盘
        if "成功" in result:
            refresh_board()  # 更新棋盘显示
        if "結束" in result:
            black_num = 0
            white_num = 0
            refresh_board()
            for i in range(8):
                for j in range(8):
                    if board[i][j] == "X":
                        black_num += 1
                    elif board[i][j] == "O":
                        white_num += 1
            if black_num > white_num:
                messagebox.showinfo("遊戲結果", "黑棋勝利！")
            else:
                messagebox.showinfo("遊戲結果", "白棋勝利！")
            server.shutdown_game(game_id,current_user)
            game_id = 0
            current_user = 0
            new_window.destroy()
    except Exception as e:
        messagebox.showerror("錯誤", f"落子失敗: {e}")

def main_gui():
    global server
    if len(sys.argv) < 1:
        print("使用方法: python client.py serverIP")
        sys.exit(1)

    server_ip = server
    server = xmlrpc.client.ServerProxy(f"http://{server_ip}:{PORT}")

    root.title('黑白棋')
    root.geometry('380x400')
    root.resizable(False, False)
    txt = tk.Label(root, textvariable=a, font=('Arial', 20), anchor='nw', width=5, height=2, pady=5)
    txt.pack()
    tk.Button(root, text="註冊", command=register_gui).pack(pady=5)
    tk.Button(root, text="登入", command=login_gui).pack(pady=5)
    tk.Button(root, text="開始遊戲", command=start_game_gui).pack(pady=5)
    tk.Button(root, text="退出", command=root.quit).pack(pady=5)
    root.mainloop()

if __name__ == "__main__":
    main_gui()
