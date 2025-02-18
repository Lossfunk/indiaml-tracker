import React from 'react';
import { motion } from 'framer-motion';
import { FaRegComment, FaRetweet, FaRegHeart, FaChartBar, FaRegBookmark, FaShare, FaCheckCircle } from 'react-icons/fa';

const tweetAnimation = {
  hidden: { opacity: 0, y: 20 },
  visible: { 
    opacity: 1,
    y: 0,
    transition: { duration: 0.6 }
  }
};

const repliesAnimation = {
  hidden: { opacity: 0 },
  visible: { 
    opacity: 1,
    transition: { 
      staggerChildren: 0.3,
      delayChildren: 0.4
    }
  }
};

const Tweet = ({ className }) => {
  return (
    <div className={`max-w-2xl mx-auto bg-gray-900 text-white ${className}`}>
      <motion.div
        className="rounded-xl overflow-hidden border border-gray-800 bg-black"
        variants={tweetAnimation}
        initial="hidden"
        whileInView="visible"
        viewport={{ once: true }}
      >
        {/* Original Tweet */}
        <div className="p-4 border-b border-gray-800">
          <div className="flex">
            <img 
              src="/api/placeholder/64/64" 
              alt="Paras Chopra" 
              className="h-12 w-12 rounded-full mr-3" 
            />
            <div className="flex-1">
              <div className="flex items-center">
                <h4 className="font-bold text-white">Paras Chopra</h4>
                <FaCheckCircle className="ml-1 text-blue-500 text-sm" />
                <span className="text-gray-500 ml-2">@paraschopra · Jan 23</span>
              </div>
              <div className="mt-2 space-y-3 text-gray-100">
                <p>i'm curious if anyone is actively tracking paper accepts from (majority) india-based teams at top conferences like ICLR, ICML or neurips?</p>
                <p>i know some indian teams who get great SOTA papers out, but they never get the spotlight.</p>
                <p>i'm happy to fund this if someone builds a tracker</p>
              </div>
              
              <div className="mt-4 flex justify-between text-gray-500">
                <div className="flex items-center">
                  <FaRegComment className="mr-2" />
                  <span>13</span>
                </div>
                <div className="flex items-center">
                  <FaRetweet className="mr-2" />
                  <span>13</span>
                </div>
                <div className="flex items-center">
                  <FaRegHeart className="mr-2" />
                  <span>328</span>
                </div>
                <div className="flex items-center">
                  <FaChartBar className="mr-2" />
                  <span>43K</span>
                </div>
                <div className="flex items-center">
                  <FaRegBookmark />
                </div>
                <div className="flex items-center">
                  <FaShare />
                </div>
              </div>
            </div>
          </div>
        </div>
        
        {/* Reply Tweet */}
        <motion.div 
          className="p-4 pl-6 border-l-4 border-gray-800"
          variants={repliesAnimation}
        >
          <div className="flex">
            <img 
              src="/api/placeholder/64/64" 
              alt="Sohan Basak" 
              className="h-12 w-12 rounded-full mr-3" 
            />
            <div className="flex-1">
              <div className="flex items-center">
                <h4 className="font-bold text-white">Sohan Basak e/code</h4>
                <span className="text-gray-500 ml-2">@HiSohan · Jan 23</span>
              </div>
              <div className="mt-2 space-y-3 text-gray-100">
                <p>Cool. Weekend project locked in if no one else has already done so.</p>
                <p>Steps:</p>
                <ol className="list-decimal pl-5 space-y-1">
                  <li>Define Majority Indian teams</li>
                  <li>Conference DBs and sources</li>
                  <li>OpneReview APIs</li>
                  <li>Aggregation and metrics crontabs</li>
                  <li>Publish.</li>
                </ol>
              </div>
              
              <div className="mt-4 flex justify-between text-gray-500">
                <div className="flex items-center">
                  <FaRegComment className="mr-2" />
                  <span>2</span>
                </div>
                <div className="flex items-center">
                  <FaRetweet className="mr-2" />
                  <span>1</span>
                </div>
                <div className="flex items-center">
                  <FaRegHeart className="mr-2" />
                  <span>13</span>
                </div>
                <div className="flex items-center">
                  <FaChartBar className="mr-2" />
                  <span>21K</span>
                </div>
                <div className="flex items-center">
                  <FaRegBookmark />
                </div>
                <div className="flex items-center">
                  <FaShare />
                </div>
              </div>
            </div>
          </div>
        </motion.div>
      </motion.div>
    </div>
  );
};

export default Tweet;