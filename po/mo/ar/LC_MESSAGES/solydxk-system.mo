??          ?      <      ?     ?     ?     ?  U   ?  	   #     -     5     L  ?   Z  ?   ?  ?   ?     ?     ?  ?   ?  M   P    ?  r   ?  ?       ?  
   	     	  ?   %	     ?	     ?	  +   ?	     ?	  ?   
  0  ?
  l       ?  *   ?  ?   ?  ?   ?  w  $  ?   ?                                       
                       	                                       Commands Description Device If you prefer to install the drivers by terminal, you can use the following commands: Important Install No internet connection Remove kernel This command will install the right driver for your wireless Broadcom adapter. Use "ddm -p broadcom" to remove the drivers from your system. This will install the PAE kernel on multi-processor systems running a 32-bit OS. Use "ddm -p pae" to remove the PAE kernel from your system. Note that you cannot remove the kernel when you are currently booted into that kernel. This will select the right drivers for your Nvidia graphical card. It will select the Bumblebee drivers in case you have a hybrid card (both Nvidia and Intel). Use "ddm -p nvidia" to remove the drivers from your system. Unexpected error Use Backports You can use this command if you want to revert back to the open Nouveau drivers. It will remove any proprietary drivers from your system. You cannot remove a booted kernel.
Please, boot another kernel and try again. You have selected to install drivers from the backports repository whenever they are available.

Although you can run more up to date software using the backports repository,
you introduce a greater risk of breakage doing so.

Are you sure you want to continue? You need an internet connection to install the additional software.
Please, connect to the internet and try again. Project-Id-Version: device-driver-manager
Report-Msgid-Bugs-To: 
PO-Revision-Date: 2017-04-09 09:18+0000
Last-Translator: Arjen Balfoort <arjenbalfoort@solydxk.com>
Language-Team: Arabic (http://www.transifex.com/solydxk/device-driver-manager/language/ar/)
Language: ar
MIME-Version: 1.0
Content-Type: text/plain; charset=UTF-8
Content-Transfer-Encoding: 8bit
Plural-Forms: nplurals=6; plural=n==0 ? 0 : n==1 ? 1 : n==2 ? 2 : n%100>=3 && n%100<=10 ? 3 : n%100>=11 && n%100<=99 ? 4 : 5;
 تعليمات الوصف الجهاز إذا كنت تفضل تثبيت التعريفات عبر الطرفية يمكنك استخدام التعليمات التالية: هام التثبيت لا يوجد اتصال بالإنترنت إزالة النواة هذا الأمر سيقوم بتثبيت التعريف المناسب لبطاقة الشبكة اللاسلكية Broadcom الخاصة بك. استخدم "ddm -p broadcom" لإزالة التعريف من نظامك. سيقوم هذا بتثبيت نواة PAE للأنظمة متعددة الأنوية على معمارية 32 بتاستخدم "ddm -p pae" لإزالة نواة PAE من نظامك. لاحظ أنه لا يمكن حذف هذه النواة إذا كنت حاليا قد أقلعت باستخدامها. سيؤدي هذا إلى تحديد التعريف الصحيح لبطاقة الرسوميات أنفيديا الخاصة بك. وسيقوم بتحديد تعريف Bumblebee في حال ما إذا كانت لديك بطاقة رسومية هجينة (أنفيديا و إنتل معا). استخدم "ddm -p nvidia" لإزالة التعريف من نظامك. خطأ غير متوقع استخدم مستودع باكبورتس يمكنك إستخدام هذه التعليمة إذا أردت العودة إلى التعريف المفتوح (Nouveau). هذا سيزيل أي تعريف خاص بالمصنع من نظامك. لا يمكنك إزالة النواة المستخدمة حاليا.
من فضلك، حاول بعد إعادة التشغيل بنواة أخرى. لقد قمت بتحديد تثبيت التعريفات من مستودع باكبورتس متى توفرت.

رغم أنه يمكنك تشغيل برامج أكثر حداثة باستخدام مستودع باكبورتس
إلّا أنه قد تزيد من إحتمالية وقوع النظام بفعل ذلك.

هل أنت متأكد أنك تريد المتابعة؟ تحتاج لاتصال بالإنترنت لتثبيت البرامج الإضافية.
من فضلك، اتّصل بالإنترنت وحاول مرة أخرى. 