??          ?   %   ?      `     a     t     ?     ?     ?     ?     ?  U   ?  	   
               3     :  
   H     S     `  ?   f  ?   ?  ?   ?     ?     ?     ?  ?   ?  M   `    ?  r   ?  %  '     M
  -   _
  	   ?
     ?
     ?
     ?
     ?
  Z   ?
            
   !     ,     2     ?     L  
   i  ?   t  ?     ?   ?  	   ?     ?     ?  ?   ?  S   F  ?   ?  |   ?                                                    	                                                       
                 Available packages Check mirrors speed Commands Country Current Description Device If you prefer to install the drivers by terminal, you can use the following commands: Important Install No internet connection Remove Remove kernel Repository Save mirrors Speed This command will install the right driver for your wireless Broadcom adapter. Use "ddm -p broadcom" to remove the drivers from your system. This will install the PAE kernel on multi-processor systems running a 32-bit OS. Use "ddm -p pae" to remove the PAE kernel from your system. Note that you cannot remove the kernel when you are currently booted into that kernel. This will select the right drivers for your Nvidia graphical card. It will select the Bumblebee drivers in case you have a hybrid card (both Nvidia and Intel). Use "ddm -p nvidia" to remove the drivers from your system. URL Unexpected error Use Backports You can use this command if you want to revert back to the open Nouveau drivers. It will remove any proprietary drivers from your system. You cannot remove a booted kernel.
Please, boot another kernel and try again. You have selected to install drivers from the backports repository whenever they are available.

Although you can run more up to date software using the backports repository,
you introduce a greater risk of breakage doing so.

Are you sure you want to continue? You need an internet connection to install the additional software.
Please, connect to the internet and try again. Project-Id-Version: device-driver-manager
Report-Msgid-Bugs-To: 
PO-Revision-Date: 2017-04-09 09:18+0000
Last-Translator: Arjen Balfoort <arjenbalfoort@solydxk.com>
Language-Team: Polish (http://www.transifex.com/solydxk/device-driver-manager/language/pl/)
Language: pl
MIME-Version: 1.0
Content-Type: text/plain; charset=UTF-8
Content-Transfer-Encoding: 8bit
Plural-Forms: nplurals=4; plural=(n==1 ? 0 : (n%10>=2 && n%10<=4) && (n%100<12 || n%100>14) ? 1 : n!=1 && (n%10>=0 && n%10<=1) || (n%10>=5 && n%10<=9) || (n%100>=12 && n%100<=14) ? 2 : 3);
 Dostępne pakiety Sprawdź szybkość serwerów zwierciadlanych Polecenia Kraj Aktualny Opis Urządzenie Jeśli wolisz instalować sterowniki w terminalu, możesz użyć następujących poleceń: Ważne Instaluj Brak sieci Usuń Usuń jądro Repozytorium Zapisz serwery zwierciadlane Szybkość Polecenie spowoduje instalację sterownika Broadcom dla urządzeń bezprzewodowych. Użycie "ddm -p broadcom"  spowoduje usunięcie sterowników. Polecenie zainstaluje jądro z obsługa PAE w systemach wieloprocesorowych 32-bitowych. Nota bene, usunięcie jądra jest niemożliwe po jego uruchomieniu. Polecenie spowoduje wybranie właściwych sterowników Nvidia. W przypadku kart hybrydowych(zarówno Nvidia, jak i Intel) zostaną wybrane sterowniki Bumblebee.
W celu usunięcia sterowników z systemu użyj:  "ddm -p nvidia" Adres URL Niespodziewany błąd Użyj "backports" Możesz użyć tego polecenia aby wrócić do otwartych sterowników Nouveau. Zostaną usunięte z systemu wszystkie sterowniki własnościowe. Nie możesz usunąć załadowanego jądra.
Wybierz inne jądro i spróbuj ponownie. Wybrałeś instalację sterowników z repozytorium "backports" o ile są dostępne.
Używając repozytorium "backports" możesz zainstalować bardziej aktualne oprogramowanie ale z większym ryzykiem uszkodzenia systemu.
Czy nadal chcesz kontynuować? Połączenie sieciowe jest niezbędne do instalacji dodatkowego oprogramowania.
Połącz się z siecią i spróbuj ponownie. 