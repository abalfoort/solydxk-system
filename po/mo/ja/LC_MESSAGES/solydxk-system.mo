??          ?   %   ?      p     q     ?     ?     ?     ?     ?     ?  U   ?  	        $     ,     C     J  
   X     c     p  "   v  ?   ?  ?   &  ?   
     ?     ?     ?  ?   	  M   ?    ?  r   ?  ?  Z     ?	     
     
     +
     /
     6
     =
  y   J
     ?
     ?
  -   ?
               )     9     L  0   S  ?   ?  J  [  /  ?     ?     ?     ?  ?     ?   ?  N  D  ?   ?                                                    	                                                      
                 Available packages Check mirrors speed Commands Country Current Description Device If you prefer to install the drivers by terminal, you can use the following commands: Important Install No internet connection Remove Remove kernel Repository Save mirrors Speed There are no repositories to save. This command will install the right driver for your wireless Broadcom adapter. Use "ddm -p broadcom" to remove the drivers from your system. This will install the PAE kernel on multi-processor systems running a 32-bit OS. Use "ddm -p pae" to remove the PAE kernel from your system. Note that you cannot remove the kernel when you are currently booted into that kernel. This will select the right drivers for your Nvidia graphical card. It will select the Bumblebee drivers in case you have a hybrid card (both Nvidia and Intel). Use "ddm -p nvidia" to remove the drivers from your system. URL Unexpected error Use Backports You can use this command if you want to revert back to the open Nouveau drivers. It will remove any proprietary drivers from your system. You cannot remove a booted kernel.
Please, boot another kernel and try again. You have selected to install drivers from the backports repository whenever they are available.

Although you can run more up to date software using the backports repository,
you introduce a greater risk of breakage doing so.

Are you sure you want to continue? You need an internet connection to install the additional software.
Please, connect to the internet and try again. Project-Id-Version: device-driver-manager
Report-Msgid-Bugs-To: 
PO-Revision-Date: 2017-04-09 09:18+0000
Last-Translator: Arjen Balfoort <arjenbalfoort@solydxk.com>
Language-Team: Japanese (http://www.transifex.com/solydxk/device-driver-manager/language/ja/)
Language: ja
MIME-Version: 1.0
Content-Type: text/plain; charset=UTF-8
Content-Transfer-Encoding: 8bit
Plural-Forms: nplurals=1; plural=0;
 有効なパッケージ ミラーの速度を確認 コマンド 国 現在 説明 デバイス ターミナルからドライバをインストールしたい場合は、次のコマンドで行う事ができます: 重要 インストール インターネットに接続できません 削除 カーネルの削除 リボジトリ ミラーを保存 速度 保存するリポジトリはありません。 このコマンドは、ワイヤレス Broadcom アダプタ用のドライバをインストールします。システムからドライバを削除するには、"ddm -p broadcom" を使用してください。 32 ビット OS を実行しているマルチプロセッサシステム上で PAE カーネルをインストールします。お使いのシステムから PAE カーネルを削除するには、"ddm -p pae" を使用して下さい。起動で使用しているカーネルは削除できないことにご注意下さい。 Nvidia グラフィックカードのドライバを選択します。それはハイブリッドカード（Nvidia・intel 両方）を持っている場合にはBumblebee ドライバを選択します。システムからドライバを削除するには。"ddm -p nvidia" を使用して下さい。 URL 予想外のエラー Backports 使用 Nouveau ドライバに戻したい場合は、次のコマンドを使用して下さい。システムから任意のプロプライエタリドライバを削除する事ができます。 起動しているカーネルは削除する事ができません。
他のカーネルで起動し、再度行って下さい。 backports リボジトリから利用可能なドライバをインストールすることを選択しました。

backports リポジトリを使用して、多くのソフトウェアを実行することができますが
それは破損を含む大きなリスクがあります。

本当に進めてもよろしいですか？ 追加のソフトウェアをインストールするにはインターネット接続が必要です。
インターネットの接続を行い、再度行って下さい。 