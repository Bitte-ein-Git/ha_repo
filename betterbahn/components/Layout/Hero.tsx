// file: betterbahn/components/Layout/Hero.tsx
import React from "react";
// import train from "../../public/train.jpg"; // This file is missing in your project

export const Hero = () => {
	return (
		<section
			className="my-10 p-6 rounded-3xl  min-h-[200px] md:min-h-[300px]   bg-cover bg-center bg-no-repeat flex flex-col items-center justify-center  bg-black/65 bg-blend-overlay"
			style={
				{
				// backgroundImage: `url(${train.src})`, // Add train.jpg to /public folder to enable
			}
			}
		>
			{/* Hauptslogan mit hervorgehobenem Text */}
			<div className="text-center text-white uppercase text-3xl md:text-4xl font-bold  tracking-wide leading-normal  ">
				Gleicher Zug, Gleiche Zeit,{" "}
				<span className="font-bold text-primary border-white bg-white px-2 py-1 ">
					Besserer Preis
				</span>
			</div>
		</section>
	);
};
