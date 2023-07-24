import cv2
import numpy as np
from skimage.filters import threshold_sauvola
from skimage import measure
import tkinter as tk
from tkinter import filedialog, ttk
from PIL import Image, ImageTk


def segmentation(image):
    file_path=filedialog.askopenfilename()
    # Wczytanie obrazu MRI
    if file_path:
        image = cv2.imread(file_path,0)

        # Zastosowanie filtru Gaussa w celu wygładzenia obrazu i usunięcia szumów
        image_blur = cv2.GaussianBlur(image, (5, 5), 0)

        # Zastosowanie operacji progowania (binaryzacja Sauvola) w celu podziału obrazu na piksele
        # należące do struktury anatomicznej i tła
        threshold = threshold_sauvola(image_blur, window_size=25, k=0.05)
        image_thresholded = (image_blur > threshold).astype('uint8') * 255

        # Zastosowanie operacji erozji i dylatacji w celu usunięcia małych nieciągłości w strukturze
        # anatomicznej i wyrównania jej granic
        kernel = np.ones((5, 5), np.uint8)
        image_eroded = cv2.erode(image_thresholded, kernel, iterations=2)
        image_dilated = cv2.dilate(image_eroded, kernel, iterations=2)
        cv2.imshow("Result", image_dilated)
        # Funkcja obsługi zdarzenia kliknięcia myszką
        def on_mouse_click(event, x, y, flags, param):
            if event == cv2.EVENT_LBUTTONDOWN:
                # Utworzenie pustego obrazu
                mask = np.zeros_like(image_dilated)
                # Znalezienie konturów na obrazie oryginalnym
                contours, hierarchy = cv2.findContours(image_dilated.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                # Znalezienie konturu, który zawiera punkt kliknięcia
                for cnt in contours:
                    if cv2.pointPolygonTest(cnt, (x, y), False) == 1:
                        # Wypełnienie konturu na masce
                        cv2.fillPoly(mask, [cnt], 255)
                # Przyłożenie maski do obrazu oryginalnego
                result = cv2.bitwise_and(image, image, mask=mask)
                # Wyświetlenie wyniku
                cv2.imshow("Result", result)
                #wstawienie wynikowego elementu wysegmentowanego do GUI
                segmented_image = Image.fromarray(result)
                segmented_image_tk = ImageTk.PhotoImage(segmented_image)
                result_label.config(image=segmented_image_tk)
                result_label.image = segmented_image_tk
                #obliczanie wsp. Fereta
                properties = measure.regionprops(image_dilated.astype(int))
                contour = properties[0].coords
                distances = np.linalg.norm(contour - np.mean(contour, axis=0), axis=1)
                feret_diameter = np.max(distances)
                print("Współczynnik Fereta:", feret_diameter)

                #tworzenie wektora cech - dodanie najwyzej i najnizej położonego punktu wyznaczonego elementu
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
                #najwyższy i najniższy punkt elementu
                lowest_point = min_loc
                higher_point = max_loc
                # zajmowana powierzchnia zaznaczonego elementu
                surface_area = np.count_nonzero(result)
                background_area = np.sum(result == 0)
                total_area=background_area+surface_area
                value_area=round(((surface_area/total_area)*100),2)
                # procent tkanki kostnej
                skeletal_area = np.count_nonzero(image_dilated)
                element_skeletal_area=round(((surface_area/skeletal_area)*100),2)

                features = []
                features.append(lowest_point)
                features.append(higher_point)
                features.append(value_area)
                print(features)
                print(surface_area)
                print(total_area)
                cechy_label = tk.Label(root, text="Wektor cech: \n", bg="#6739D4", fg="#D6D1E1", font=("Arial", 16),
                                       bd=3, relief="ridge", pady=20)
                cechy_label.pack()
                def reset():
                    # Usuwanie zawartości labela z wynikami
                    cechy_label.pack_forget()
                    reset_button.pack_forget()

                reset_button = tk.Button(root, text="Reset", command=reset,
                                 bg="#6739D4", fg="#D6D1E1", font=("Arial", 16), bd=3, relief="ridge")

                def update_cechy_label(lowest_point, higher_point, value_area):
                    cechy_label.config(text="Wektor cech: \n" + "Najniżej położony punkt: " + str(
                        lowest_point) + "\n Najwyżej położony punkt: " + str(higher_point) +
                                            "\n Współczynnik Fereta: " + str(round(feret_diameter, 2)) +
                                            "\n Procent tkanki kostnej [%]: " + str(round(element_skeletal_area, 2)) +
                                            "\n Powierzchnia wyznaczonego elementu [%]: " + str(value_area))

                update_cechy_label(lowest_point, higher_point, value_area)
                reset_button.pack()

        # Utworzenie okna z obrazem
        cv2.namedWindow("MRI")

        # Dodanie funkcji obsługi zdarzenia kliknięcia myszką
        cv2.setMouseCallback("MRI", on_mouse_click)

        # Wyświetlenie obrazu
        cv2.imshow("MRI", image)

        cv2.waitKey(0)
        cv2.destroyAllWindows()
        segmented_image=Image.fromarray(image)
    return segmented_image


def segment_image_click():
    image = cv2.imread(filename_entry.get(), 0)
    segmented_image = segmentation(image)


root = tk.Tk()
root.title('Segmentacja')
root.geometry("1200x1000")
root.configure(bg="#331C6A")

label = tk.Label(root, text="APLIKACJA SEGMENTUJĄCA RDZEŃ KRĘGOWY", font=("Arial", 20),
                 bg="#331C6A", fg="#D6D1E1")
label.pack(pady=20)

filename_entry = tk.Entry(root)

segment_button = tk.Button(root, text="Segmentuj", command=segment_image_click,
                           bg="#6739D4", fg="#D6D1E1", font=("Arial", 16),bd=3, relief="ridge")
segment_button.pack()


result_label = tk.Label(root, bg="#331C6A")
result_label.pack()
root.mainloop()
