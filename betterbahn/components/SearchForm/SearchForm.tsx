"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { extractUrlFromText } from "./extractUrlFromText";
import { URLInput } from "./URLInput";
import { useSearchFormData } from "./useSearchFormData";

export const SearchForm = () => {
	const router = useRouter();
	const [url, setUrl] = useState("");
	const [urlParseError, setUrlParseError] = useState<string | null>(null);
	const { formData, updateFormData } = useSearchFormData();

	const handleUrlParsingAndNavigation = () => {
		if (!url.trim()) {
			setUrlParseError(
				"Bitte geben Sie Text mit einer DB-Buchungs-URL ein oder fügen Sie einen direkten DB-Buchungslink ein"
			);
			return;
		}

		const extractedUrl = extractUrlFromText(url);

		if (!extractedUrl) {
			setUrlParseError(
				"Keine gültige DB-Buchungs-URL gefunden. Bitte fügen Sie Text mit einem Deutsche Bahn Buchungslink ein (von bahn.de mit /buchung/start Pfad) oder überprüfen Sie, ob Ihre URL korrekt ist."
			);
			return;
		}

		const searchParams = new URLSearchParams({
			url: extractedUrl,
			bahnCard: formData.bahnCard,
			hasDeutschlandTicket: String(formData.hasDeutschlandTicket),
			passengerAge: String(formData.passengerAge),
			travelClass: formData.travelClass,
			// autoSearch: "true", // Flag to indicate auto-search should happen
		});

		router.push(`/discount?${searchParams.toString()}`);
	};

	return (
		<section>
			{/* Unified Input and Search Section */}
			<div className="space-y-6">
				<URLInput url={url} setUrl={setUrl} />
				<div className="flex flex-col md:flex-row gap-8">
					<select
						value={formData.bahnCard}
						onChange={(e) => updateFormData({ bahnCard: e.target.value })}
						className="w-full px-3 py-2 resize-vertical border-b-2 border-gray-300 focus:ring-2 focus:ring-primary"
					>
						<option className="text-black" value="none">Keine BahnCard</option>
						<option className="text-black" value="25">BahnCard 25 </option>
						<option className="text-black" value="50">BahnCard 50 </option>
					</select>
					<input
						type="number"
						value={formData.passengerAge}
						onChange={(e) => updateFormData({ passengerAge: e.target.value })}
						placeholder="Alter des Reisenden"
						min="0"
						max="120"
						className="w-full px-3 py-2 resize-vertical border-b-2 border-gray-300 focus:ring-2 focus:ring-primary"
					/>
					<select
						value={String(formData.hasDeutschlandTicket)}
						onChange={(e) =>
							updateFormData({
								hasDeutschlandTicket: e.target.value === "true",
							})
						}
						className="w-full px-3 py-2 resize-vertical border-b-2 border-gray-300 focus:ring-2 focus:ring-primary"
					>
						<option className="text-black" value="true">Deutschlandticket</option>
						<option className="text-black" value="false">Kein Deutschlandticket</option>
					</select>
					<select
						value={String(formData.travelClass)}
						onChange={(e) =>
							updateFormData({
								travelClass: e.target.value,
							})
						}
						className="w-full px-3 py-2 resize-vertical border-b-2 border-gray-300 focus:ring-2 focus:ring-primary"
					>
						<option className="text-black" value="1">Erste Klasse</option>
						<option className="text-black" value="2">Zweite Klasse</option>
					</select>
				</div>

				<button
					onClick={handleUrlParsingAndNavigation}
					disabled={!url.trim()}
					className="w-full bg-primary text-white py-3 px-4 rounded-full hover:cursor-pointer hover:bg-primary/80 disabled:opacity-50 disabled:cursor-not-allowed transition-colors text-lg font-semibold"
				>
					Bessere Verbindung suchen
				</button>
			</div>

			{urlParseError && (
				<div className="mt-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded">
					<strong>Fehler:</strong> {urlParseError}
				</div>
			)}
		</section >
	);
};
