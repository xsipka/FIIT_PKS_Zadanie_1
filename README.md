# Komunikácia s využitím UDP protokolu

Zadanie:

• Navrhnúť a implementovať program s použitím vlastného protokolu nad protokolom UDP transportnej vrstvy sieťového modelu TCP/IP.

• Program umožní prenos textových správ a ľubovoľného binárneho súboru medzi dvoma počítačmi.

• Program bude pozostávať z vysielacej a prijímacej časti. Vysielací uzol pošle súbor inému uzlu v sieti. 
Predpokladá sa, že v sieti dochádza k stratám dát. 

• Používateľ musí mať možnosť zadať maximálnu veľkosť fragmentu. Ak je posielaný súbor väčší, 
rozloží sa na jednotlivé fragmenty, ktoré sa pošlú samostatne.

• Po prijatí fragmentu prijímateľ vypíše správu s poradím a či bol prenesený bez chýb.

• Ak dôjde k chybe, tak musí byť možné znovuvyžiadanie chybných fragmentov.

• Pri nečinnosti komunikátor automaticky odošle paket pre udržanie spojenia každých 20-60s pokiaľ používateľ neukončí spojenie.
