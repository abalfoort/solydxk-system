??          ?   %   ?      `     a     t     ?     ?     ?     ?     ?  U   ?  	   
               3     :  
   H     S     `  ?   f  ?   ?  ?   ?     ?     ?     ?  ?   ?  M   `    ?  r   ?  ?  '     ?	     ?	  
   ?	     ?	  	    
     

     
  ^   
     {
  	   ?
     ?
     ?
     ?
     ?
     ?
  	   ?
  ?   ?
  ?   x  ?   Q               ,  ?   D  Y   ?    @  x   X                                                    	                                                       
                 Available packages Check mirrors speed Commands Country Current Description Device If you prefer to install the drivers by terminal, you can use the following commands: Important Install No internet connection Remove Remove kernel Repository Save mirrors Speed This command will install the right driver for your wireless Broadcom adapter. Use "ddm -p broadcom" to remove the drivers from your system. This will install the PAE kernel on multi-processor systems running a 32-bit OS. Use "ddm -p pae" to remove the PAE kernel from your system. Note that you cannot remove the kernel when you are currently booted into that kernel. This will select the right drivers for your Nvidia graphical card. It will select the Bumblebee drivers in case you have a hybrid card (both Nvidia and Intel). Use "ddm -p nvidia" to remove the drivers from your system. URL Unexpected error Use Backports You can use this command if you want to revert back to the open Nouveau drivers. It will remove any proprietary drivers from your system. You cannot remove a booted kernel.
Please, boot another kernel and try again. You have selected to install drivers from the backports repository whenever they are available.

Although you can run more up to date software using the backports repository,
you introduce a greater risk of breakage doing so.

Are you sure you want to continue? You need an internet connection to install the additional software.
Please, connect to the internet and try again. Project-Id-Version: device-driver-manager
Report-Msgid-Bugs-To: 
PO-Revision-Date: 2017-04-09 09:18+0000
Last-Translator: Arjen Balfoort <arjenbalfoort@solydxk.com>
Language-Team: Norwegian Bokmål (http://www.transifex.com/solydxk/device-driver-manager/language/nb/)
Language: nb
MIME-Version: 1.0
Content-Type: text/plain; charset=UTF-8
Content-Transfer-Encoding: 8bit
Plural-Forms: nplurals=2; plural=(n != 1);
 Tilgjengelige pakker Sjekk speilhastighet Kommandoer Land Gjeldende Beskrivelse Enhet Hvis du foretrekker å installere driverne via en terminal, kan du bruke følgende kommandoer: Viktig Installer Ingen internettforbindelse Fjern Fjern kjerne Pakkebrønn Lagre speil Hastighet Denne kommandoen vil installere den riktige driveren for ditt trådløse Broadcom-adapter. Bruk "ddm -p broadcom" for å fjerne driverne fra systemet ditt. Dette vil installere PAE-kjernen på multi-prosessor systemer som kjører et 32-bits OS. Bruk "ddm -p pae" for å fjerne PAE-kjernen fra systemet. Merk at du ikke kan fjerne kjernen når du har startet opp med denne. Dette vil velge de riktige driverne for ditt Nvidia-kort. Det vil velge Bumblebee-drivere dersom du har et hybrid-kort (både Nvidia og Intel). Bruk "ddm -p nvidia" for å fjerne driverne fra systemet. URL Uventet feil Bruk tilbakeporteringer Du kan bruke denne kommandoen hvis du ønsker å tilbakestille systemet til de åpne Nouveau-driverne. Det vil fjerne alle proprietære driver fra systemet ditt. Du kan ikke fjerne en kjerne som kjører.
Vennligst start en annen kjerne og prøv igjen. Du har valgt å installere drivere fra arkivet for tilbakeporteringer når disse er tilgjengelig.

Selv om du kan kjøre mer oppdatert programvare ved å bruke arkivet for tilbakeporteringer
øker du risikoen for at noe kan slutte å virke.

Er du sikker på at du vil fortsette? Du trenger en internettforbindelse for å installere tilleggsprogramvaren.
Vennligst koble til internett og prøv igjen. 