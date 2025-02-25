import React from 'react';
import { motion } from 'framer-motion';
import { FaTwitter, FaHandshake, FaLightbulb, FaGlobeAsia, FaCode } from 'react-icons/fa';
import Tweet from './Tweet';

// Animation variants
const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.3,
      delayChildren: 0.2,
    },
  },
};

const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.5 },
  },
};

const storyCardVariants = {
  hidden: { opacity: 0, x: -30 },
  visible: (i) => ({
    opacity: 1,
    x: 0,
    transition: { duration: 0.6, delay: i * 0.2 },
  }),
};

// Story milestones
const storyMilestones = [
  {
    icon: <FaTwitter className="text-blue-400 text-2xl" />,
    title: "The Tweet That Started It All",
    content: "Paras Chopra, CEO of Wingify, tweeted asking if anyone was interested in building a platform to track India's contributions to machine learning."
  },
  {
    icon: <FaCode className="text-green-400 text-2xl" />,
    title: "From Idea to Reality",
    content: "Sohan Basak, who loves tech and just writing code, responded to the challenge and quickly built the first version of the tracker."
  },
  {
    icon: <FaHandshake className="text-yellow-400 text-2xl" />,
    title: "Collaboration Begins",
    content: "After Paras retweeted the project, they exchanged contacts and formed a partnership to develop the platform further."
  },
  {
    icon: <FaGlobeAsia className="text-purple-400 text-2xl" />,
    title: "Focused on Local Innovation",
    content: "The team decided to specifically track ML research conducted within India, highlighting domestic innovation rather than diaspora contributions."
  }
];

const Motivation = () => {
  return (
    <section className="bg-gray-900 py-16 px-4">
      <motion.div 
        className="max-w-5xl mx-auto"
        variants={containerVariants}
        initial="hidden"
        whileInView="visible"
        viewport={{ once: true }}
      >
        {/* Section Header */}
        <motion.div 
          className="text-center mb-16"
          variants={itemVariants}
        >
          <FaLightbulb className="text-yellow-400 text-4xl mx-auto mb-4" />
          <h2 className="text-3xl font-bold text-white mb-4">Our Motivation</h2>
          <div className="w-24 h-1 bg-indigo-500 mx-auto mb-6"></div>
          <p className="text-gray-300 text-lg max-w-3xl mx-auto">
            The IndiaML Tracker was born from a simple tweet and grew into a mission to spotlight 
            India's contributions to the global machine learning landscape.
          </p>
        </motion.div>

        {/* Story Timeline with tweet in background */}
        <div className="relative mb-16">
          {/* Background Tweet (scaled down and positioned behind) */}
          <div className="absolute opacity-10 transform scale-75 -rotate-2 blur-sm left-0 right-0 mx-auto w-full max-w-md pointer-events-none">
            <Tweet />
          </div>
          
          {/* Main Story Timeline */}
          <div className="relative z-10">
            {storyMilestones.map((milestone, index) => (
              <motion.div
                key={index}
                className="flex mb-12 md:mb-8 items-start"
                variants={storyCardVariants}
                custom={index}
              >
                <div className="mr-4 mt-1 bg-gray-800 p-3 rounded-full">
                  {milestone.icon}
                </div>
                <div className="bg-gray-800 rounded-lg p-6 flex-1 shadow-lg transform hover:scale-105 transition-transform">
                  <h3 className="text-xl font-semibold text-white mb-2">
                    {milestone.title}
                  </h3>
                  <p className="text-gray-300">
                    {milestone.content}
                  </p>
                </div>
              </motion.div>
            ))}
          </div>
        </div>

        {/* Tweet Callout (smaller version) */}
        <motion.div 
          className="mb-16 max-w-lg mx-auto"
          variants={itemVariants}
        >
          <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
            <div className="flex items-center mb-4">
              <FaTwitter className="text-blue-400 mr-3 text-xl" />
              <p className="text-gray-300 italic text-sm">
                "i'm happy to fund this if someone builds a tracker" 
                <a href="https://x.com/paraschopra" className="text-blue-400 ml-1">@paraschopra</a>
              </p>
            </div>
            <div className="flex items-center">
              <FaTwitter className="text-blue-400 mr-3 text-xl" />
              <p className="text-gray-300 italic text-sm">
                "Cool. Weekend project locked in if no one else has already done so."
                <a href="https://x.com/HiSohan" className="text-blue-400 ml-1">@HiSohan</a>
              </p>
            </div>
            <p className="text-gray-400 text-xs mt-4 text-right">January 23, 2023</p>
          </div>
        </motion.div>

        {/* Mission Statement */}
        <motion.div 
          className="bg-gradient-to-r from-indigo-900 to-purple-900 rounded-xl p-8 shadow-2xl"
          variants={itemVariants}
        >
          <blockquote className="text-xl text-gray-100 italic relative">
            <span className="text-5xl text-indigo-300 absolute top-0 left-0 opacity-20">"</span>
            <p className="relative z-10 pl-6">
              We're committed to showcasing the groundbreaking machine learning research happening 
              within India's borders. By spotlighting local innovation, we aim to inspire the next 
              generation of researchers and position India as a global leader in AI advancement.
            </p>
            <footer className="mt-4 text-right">
              <div className="font-medium text-indigo-300">The IndiaML Tracker Team</div>
            </footer>
          </blockquote>
        </motion.div>

        {/* Call to Action */}
        <motion.div 
          className="text-center mt-16"
          variants={itemVariants}
        >
          <h3 className="text-2xl font-semibold text-white mb-6">Join Us in Mapping India's ML Journey</h3>
          <div className="flex flex-wrap justify-center gap-4">
            <button className="bg-indigo-600 hover:bg-indigo-700 text-white px-6 py-3 rounded-md transition-colors">
              Submit Research
            </button>
            <button className="bg-transparent border-2 border-indigo-500 text-indigo-300 hover:bg-indigo-900 px-6 py-3 rounded-md transition-colors">
              Learn More
            </button>
          </div>
        </motion.div>
      </motion.div>
    </section>
  );
};

export default Motivation;