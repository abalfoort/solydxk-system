??          ?   %   ?      @     A     U     ^     f     n     z  U   ?  	   ?     ?     ?     ?       
        !  ?   '  ?   ?  ?   ?     t     x     ?  ?   ?  M   !    o  r   u  ?  ?     q	     ?	     ?	     ?	  
   ?	     ?	  g   ?	     "
     *
     .
     ;
     W
     g
     l
  ?   q
  ?     ?        ?     ?     ?  ?   ?  w   ?    ?  ?                                                                                   
                             	                 Check mirrors speed Commands Country Current Description Device If you prefer to install the drivers by terminal, you can use the following commands: Important Install Logging No internet connection Remove kernel Repository Speed This command will install the right driver for your wireless Broadcom adapter. Use "ddm -p broadcom" to remove the drivers from your system. This will install the PAE kernel on multi-processor systems running a 32-bit OS. Use "ddm -p pae" to remove the PAE kernel from your system. Note that you cannot remove the kernel when you are currently booted into that kernel. This will select the right drivers for your Nvidia graphical card. It will select the Bumblebee drivers in case you have a hybrid card (both Nvidia and Intel). Use "ddm -p nvidia" to remove the drivers from your system. URL Unexpected error Use Backports You can use this command if you want to revert back to the open Nouveau drivers. It will remove any proprietary drivers from your system. You cannot remove a booted kernel.
Please, boot another kernel and try again. You have selected to install drivers from the backports repository whenever they are available.

Although you can run more up to date software using the backports repository,
you introduce a greater risk of breakage doing so.

Are you sure you want to continue? You need an internet connection to install the additional software.
Please, connect to the internet and try again. Project-Id-Version: device-driver-manager
Report-Msgid-Bugs-To: 
PO-Revision-Date: 2017-05-28 21:02+0000
Last-Translator: Butterfly <gokhanlnx@gmail.com>
Language-Team: Turkish (http://www.transifex.com/solydxk/device-driver-manager/language/tr/)
Language: tr
MIME-Version: 1.0
Content-Type: text/plain; charset=UTF-8
Content-Transfer-Encoding: 8bit
Plural-Forms: nplurals=2; plural=(n > 1);
 Yansı hızlarını kontrol et Komutlar Ülke Şimdiki Açıklama Aygıt Eğer sürücüleri uçbirim yardımıyla kurmak isterseniz, aşağıdaki komutları kullanabilirsiniz: Önemli Kur Günlükleme İnternet bağlantısı yok Çekirdeği sil Depo Hız Bu komut Broadcom kablosuz ağ sürücüsü için doğru sürücüyü seçecektir. Sürücüyü sistemden silmek için "ddm -p broadcom" komutunu kullanınız. Bu çoklu-çekirdek üstünde çalışan 32 bit işletim sistemi için PAE çekirdeği kurar. PAE çekirdeği sistemden silmek için "ddm -p pae" komutunu kullanınız. Eğer şu an sisteminizi PAE çekirdek ile açtı iseniz silemezsiniz. Bu Nvidia grafik kartı için doğru sürücüyü seçecektir. (Nvidia + Intel) hibrit kartlar olması durumunda Bumblebee seçilecektir. Sürücüyü sistemden silmek için "ddm -p nvidia" komutunu kullanınız. URL Beklenmedik hata Backports kullan Açık kaynak Nouveau sürücüsüne dönmek isterseniz bu komutu kullanabilirsiniz. Bu tüm sahipli sürücüyü sisteminizden siler. Açılış yapılan bir çekirdeği silemezsiniz.
Lütfen, başka bir çekirdekle açılış yapın ve yeniden deneyin. Backport deposundan seçtiğiniz sürücüler kullanılabilir olduğunda yüklenecektir.

Bununla birlikte güncel yazılımları, backports depolarını kullanarak çalıştırabilirsiniz.

Bunu yaparken bozulma riski yüksektir.

Devam etmek istediğinizden eminmisiniz? Ek yazılımları kurmak için bir internet bağlantısına ihtiyacınız var.
Lütfen, internet bağlantısı kurun ve yeniden deneyin. 