??            )   ?      ?     ?     ?     ?     ?     ?     ?     ?  U   ?  	   :     D     L     T     k     r  
   ?     ?     ?  "   ?  ?   ?  ?   N  ?   2               #  ?   1  M   ?    	  r     '  ?     ?
  0   ?
     ?
     
          &     7  ?   L               1  3   H     |     ?     ?  !   ?     ?  ;   ?  ?   )  ?    T  ?  
   Q  #   \  '   ?    ?  ?   ?  ?  [    #                                                                
                                                      	                    Available packages Check mirrors speed Commands Country Current Description Device If you prefer to install the drivers by terminal, you can use the following commands: Important Install Logging No internet connection Remove Remove kernel Repository Save mirrors Speed There are no repositories to save. This command will install the right driver for your wireless Broadcom adapter. Use "ddm -p broadcom" to remove the drivers from your system. This will install the PAE kernel on multi-processor systems running a 32-bit OS. Use "ddm -p pae" to remove the PAE kernel from your system. Note that you cannot remove the kernel when you are currently booted into that kernel. This will select the right drivers for your Nvidia graphical card. It will select the Bumblebee drivers in case you have a hybrid card (both Nvidia and Intel). Use "ddm -p nvidia" to remove the drivers from your system. URL Unexpected error Use Backports You can use this command if you want to revert back to the open Nouveau drivers. It will remove any proprietary drivers from your system. You cannot remove a booted kernel.
Please, boot another kernel and try again. You have selected to install drivers from the backports repository whenever they are available.

Although you can run more up to date software using the backports repository,
you introduce a greater risk of breakage doing so.

Are you sure you want to continue? You need an internet connection to install the additional software.
Please, connect to the internet and try again. Project-Id-Version: device-driver-manager
Report-Msgid-Bugs-To: 
PO-Revision-Date: 2017-04-10 23:27+0000
Last-Translator: Михаил Ильинский <mail@milinsky.com>
Language-Team: Russian (http://www.transifex.com/solydxk/device-driver-manager/language/ru/)
Language: ru
MIME-Version: 1.0
Content-Type: text/plain; charset=UTF-8
Content-Transfer-Encoding: 8bit
Plural-Forms: nplurals=4; plural=(n%10==1 && n%100!=11 ? 0 : n%10>=2 && n%10<=4 && (n%100<12 || n%100>14) ? 1 : n%10==0 || (n%10>=5 && n%10<=9) || (n%100>=11 && n%100<=14)? 2 : 3);
 Доступные пакеты Проверить скорость зеркал Команды Страна Текущий Описание Устройство Если вы предпочитаете установить драйверы с помощью терминала, вы можете использовать следующие команды: Важный Установить Логирование Нет подключения к интернету Удалить Удалить ядра Репозиторий Сохранить зеркала Скорость Нет репозиториев для сохранения Эта команда установит нужный драйвер для вашего беспроводного адаптера Broadcom. Используйте "ddm -p broadcom" для удаления драйвера из системы. Это позволит установить pae-ядро для многопроцессорных систем под управлением 32-разрядной ОС. Использовать "ddm -p pae", чтобы удалить ядро pae из вашей системы. Обратите внимание, что нельзя удалить ядро, когда вы находитесь в сессии запущенной в нем в текущий момент. Это позволит выбрать правильные драйверы для видеокарты NVIDIA. Он подберет Bumblebee  в случае, если у вас гибридная карта (как NVIDIA и Intel). Используйте "ddm -p nvidia" чтобы удалить драйверы из системы. Адрес Неожиданная ошибка Использовать бэкпорт Вы можете использовать эту команду, если вы хотите вернуться к открытым драйверам. Это удалит любые проприетарные драйверы из вашей системы Вы не можете удалить запущенные ядра.
Пожалуйста, загрузитесь с другого ядра и попробуйте снова. Вами выбрана установка драйверов из репозитория бэкпортов, если они доступны.

Хотя используя бэкпорт-репозитории Вы можете работать со свежими версиями программного обеспечения, Вы делаете это на свой страх и риск.

Уверены, что хотите продолжить? Вам нужно подключение к интернету для установки дополнительного программного обеспечения.
Пожалуйста, подключитесь к Интернету и повторите попытку 