"""Optimizer Step website content: site facts, tracks, labs, videos and FAQs.

Edit the words here, then run `python scripts/build_pages.py` to rebuild /docs.
Keep facts true: the build publishes everything in this file.
"""

SITE = {
    "name": "Optimizer Step",
    "url": "https://www.optimizerstep.com",
    "email": "admin@optimizerstep.com",
    "tagline": "Make the model make sense.",
    "youtube": "https://www.youtube.com/@optimizerstep",
    "instagram": "https://www.instagram.com/optimizerstep/",
    "linkedin": "https://www.linkedin.com/in/kalluri-venkatesh-3a2046204/",
    "x": "https://x.com/optimizerstep",
    "x_handle": "@optimizerstep",
    "instructor": "Kalluri Venkatesh",
    "instructor_first": "Venkatesh",
    "subscribers": "4,300+",
    "videos": "120+",
    "capacity": 100,
    # planned_price / price_* are filled in from PRICE_TIERS further down.
    "policy_updated": "20 November 2026",
    # Meta Business settings > Brand safety > Domains: proves to Meta that the Optimizer Step
    # business portfolio owns optimizerstep.com. Keep it in <head> on the home page.
    "facebook_domain_verification": "jmv9t7o5fqeidwmqgq9tad9666v746",
}

# YouTube videos from the Optimizer Step channel used on track and lab pages.
# hindi=True only where the YouTube title itself says the video is in Hindi.
VIDEOS = {
    "D37cTKjtXvU": {"title": "Welcome to Optimizer Step: learn AI and ML with maths, theory, coding and projects"},
    "I0UKTp3-ndg": {"title": "Python for AI/ML beginners: learn only what you actually need"},
    "ajsZtbeUxGs": {"title": "The only maths you need for AI/ML: a beginner roadmap"},
    "9tOL3HL1dxo": {"title": "Complete AI/ML laptop setup: Python, Miniconda, VS Code, Jupyter"},
    "IyYEGcmmaak": {"title": "Gradient descent: why one number breaks AI training", "hindi": True},
    "U_wsdhuWNNg": {"title": "I gave an AI only wrong answers. It scored 100% (overfitting)", "hindi": True},
    "v1hW3qx8B98": {"title": "Backpropagation: what loss.backward() really does", "hindi": True},
    "Ls7wg-NQ5Os": {"title": "Activation functions: 2,513 weights lost to 3 weights", "hindi": True},
    "AZ0jMY8ADXA": {"title": "SGD vs Momentum vs Adam: optimizers explained visually", "hindi": True},
    "PkXMxcr6EnE": {"title": "Why my neural network failed the exam (PyTorch)", "hindi": True},
    "LcyPUf5G8ks": {"title": "Scalars, vectors, matrices and tensors explained"},
    "FxMcnUEBBTs": {"title": "Vectors explained for AI/ML beginners: how AI sees data"},
    "vd40uSemRrE": {"title": "Dot product vs cosine similarity: which one finds the better match?"},
    "9rOP9QWqjYo": {"title": "Local RAG pipeline, part 3: text embeddings in Python"},
    "0tAXcUa4wRU": {"title": "Local RAG pipeline from scratch, part 1: architecture and setup"},
    "c5FX2rCTYKs": {"title": "Local RAG pipeline, part 2: PDF extraction and chunking"},
    "-oKrOiQFYEk": {"title": "RAG pipeline, part 4: semantic search with ChromaDB"},
    "ez6soUPWtL4": {"title": "A RAG pipeline that cites its sources accurately"},
}

TRACKS = [
    {
        "id": "foundations",
        "slug": "ml-foundations",
        "seo_title": "ML Foundations: Machine Learning Course for Beginners",
        "icon": "∑",
        "level": "Beginner",
        "title": "ML Foundations",
        "tagline": "Understand the algorithms before you reach for a library.",
        "intro": "Start from zero and learn how machine learning really works: how data becomes features, how a model learns with gradient descent, and how to tell whether it is any good.",
        "tags": ["Python", "NumPy", "Scikit-learn", "Regression"],
        "modules": [
            ("Data, features and train/test splits", "Turn raw data into features, split it honestly, and avoid fooling yourself with leaked information."),
            ("Regression and gradient descent", "Fit lines and curves, define a loss, and watch gradient descent minimize it step by step."),
            ("Classification, trees and evaluation", "Predict categories, read a confusion matrix, and choose metrics that match the problem."),
            ("Model selection and practical pitfalls", "Spot overfitting, use validation data, and pick a model you can defend."),
        ],
        "project": "Predict a real-world outcome and explain the model.",
        "project_detail": "You will take a real dataset from raw table to trained model, then explain which features drive the predictions and where the model goes wrong.",
        "audience": "Complete beginners, students and developers who want solid fundamentals before deep learning.",
        "background": "Basic coding familiarity helps. The track starts with the core ideas and guided Python examples.",
        "lab": "gradient-descent",
        "videos": ["I0UKTp3-ndg", "ajsZtbeUxGs", "IyYEGcmmaak", "U_wsdhuWNNg"],
    },
    {
        "id": "deep-learning",
        "slug": "deep-learning-vision",
        "seo_title": "Deep Learning & Computer Vision Course with PyTorch",
        "icon": "◈",
        "level": "Intermediate",
        "title": "Deep Learning & Vision",
        "tagline": "Build neural networks and make images useful.",
        "intro": "Go from tensors and autograd to convolutional networks. Build a neural network by hand first, then train and debug real image models in PyTorch.",
        "tags": ["PyTorch", "Neural networks", "CNNs", "Computer vision"],
        "modules": [
            ("Tensors, autograd and training loops", "Learn the PyTorch building blocks and write a training loop you understand line by line."),
            ("Neural networks from scratch", "Build layers, activations and backpropagation by hand, so nothing is a black box."),
            ("Convolutional models for images", "See how convolutions pick out edges and shapes, and build a CNN that classifies images."),
            ("Transfer learning and model debugging", "Reuse pretrained models and diagnose the bugs that make training fail."),
        ],
        "project": "Train an image classifier with PyTorch.",
        "project_detail": "You will train, evaluate and debug an image classifier in PyTorch, then improve it with transfer learning.",
        "audience": "Learners who know Python and the ML basics and want to understand deep learning properly.",
        "background": "Comfortable with Python. ML Foundations or similar experience recommended.",
        "lab": "decision-boundary",
        "videos": ["v1hW3qx8B98", "Ls7wg-NQ5Os", "AZ0jMY8ADXA", "PkXMxcr6EnE"],
    },
    {
        "id": "nlp",
        "slug": "nlp-transformers",
        "seo_title": "NLP & Transformers Course: Embeddings and Attention",
        "icon": "⌘",
        "level": "Intermediate",
        "title": "NLP & Transformers",
        "tagline": "Turn text into useful signals and understand attention.",
        "intro": "Learn how machines read: tokens, embeddings, similarity and the attention mechanism behind transformers. Then build a text classifier and study the mistakes it makes.",
        "tags": ["NLP", "Embeddings", "Attention", "Transformers"],
        "modules": [
            ("Tokenization and text features", "Split text into tokens and turn words into numbers a model can use."),
            ("Embeddings and semantic similarity", "Represent meaning as vectors and measure how close two pieces of text are."),
            ("Attention and transformer intuition", "Understand how attention decides which words matter: the core idea behind transformers."),
            ("Text classification and evaluation", "Build a classifier, evaluate it fairly, and learn from the examples it gets wrong."),
        ],
        "project": "Build a text classifier and inspect its errors.",
        "project_detail": "You will build a text classifier, measure it honestly, and dig into the examples it misclassifies to understand why.",
        "audience": "Learners who want to understand the ideas behind modern language models, not just call an API.",
        "background": "Python and ML Foundations-level knowledge recommended.",
        "lab": "attention",
        "videos": ["FxMcnUEBBTs", "vd40uSemRrE", "9rOP9QWqjYo"],
    },
    {
        "id": "rag",
        "slug": "rag",
        "seo_title": "RAG Course: Build LLM Apps on Your Own Data",
        "icon": "▤",
        "level": "Advanced",
        "title": "Build with RAG",
        "tagline": "Connect language models to your own knowledge base.",
        "intro": "Build retrieval-augmented generation the careful way: prepare documents, retrieve the right chunks, generate grounded answers with citations, and measure where the system fails.",
        "tags": ["RAG", "Vector search", "LLMs", "Evaluation"],
        "modules": [
            ("Chunking and document preparation", "Extract text from real documents and split it into chunks that retrieve well."),
            ("Retrieval and vector similarity", "Embed chunks, search a vector store, and tune retrieval quality."),
            ("Grounded generation and citations", "Prompt a language model to answer only from retrieved sources, with citations."),
            ("Evaluate answers and failure cases", "Measure answer quality and find the failure cases before your users do."),
        ],
        "project": "Create a grounded question-answering workflow.",
        "project_detail": "You will build a question-answering system over your own documents that cites its sources, then evaluate where it breaks.",
        "audience": "Developers who want to build reliable LLM applications on their own data.",
        "background": "Comfortable with Python and APIs. NLP basics help.",
        "lab": "attention",
        "videos": ["0tAXcUa4wRU", "c5FX2rCTYKs", "-oKrOiQFYEk", "ez6soUPWtL4"],
    },
]

LABS = [
    {
        "id": "regression",
        "slug": "gradient-descent",
        "number": "01",
        "nav": "Gradient Descent",
        "name": "Gradient descent visualizer",
        "chip": "REGRESSION",
        "h1": "Watch gradient descent <em>learn a curve.</em>",
        "lead": "Add or drag points, then watch gradient descent fit a curve one step at a time. Change the learning rate to see training converge, crawl or explode.",
        "card": "Drag points and watch a model fit them one optimizer step at a time. Push the learning rate until training explodes.",
        "title": "Gradient Descent Visualizer: Interactive Demo",
        "description": "Interactive gradient descent visualizer: add points, change the learning rate and polynomial degree, and watch the loss fall step by step. Free and runs in your browser.",
        "track": "foundations",
        "videos": ["IyYEGcmmaak", "AZ0jMY8ADXA"],
    },
    {
        "id": "boundary",
        "slug": "decision-boundary",
        "number": "02",
        "nav": "Decision Boundary",
        "name": "Decision boundary visualizer",
        "chip": "CLASSIFICATION",
        "h1": "Paint data and see the <em>decision boundary.</em>",
        "lead": "Paint two classes of points and compare how k-nearest neighbours, logistic regression and a small neural network draw the line between them.",
        "card": "Paint two classes and compare how KNN, logistic regression and a small neural network separate them, including XOR.",
        "title": "Decision Boundary Visualizer: KNN, Logistic, Neural Net",
        "description": "Paint two classes of points and compare the decision boundaries of k-nearest neighbours, logistic regression and a small neural network. Free interactive lab.",
        "track": "deep-learning",
        "videos": ["Ls7wg-NQ5Os", "v1hW3qx8B98"],
    },
    {
        "id": "clusters",
        "slug": "k-means",
        "number": "03",
        "nav": "K-Means Clustering",
        "name": "K-means clustering visualizer",
        "chip": "CLUSTERING",
        "h1": "Watch k-means <em>find the clusters.</em>",
        "lead": "Step through k-means clustering: points join their nearest centroid, then each centroid moves to the middle of its group.",
        "card": "Step through k-means: watch centroids move, inertia fall, and see why rings break the algorithm.",
        "title": "K-Means Clustering Visualizer: Interactive Demo",
        "description": "Step through k-means clustering in your browser. Change K and the dataset, watch centroids move and inertia fall, and see where k-means fails.",
        "track": "foundations",
        "videos": ["FxMcnUEBBTs"],
    },
    {
        "id": "attention",
        "slug": "attention",
        "number": "04",
        "nav": "Text Attention",
        "name": "Attention visualizer",
        "chip": "NLP",
        "h1": "See how attention <em>weighs words.</em>",
        "lead": "Type a short phrase, choose a word, and inspect a simplified attention map: similarity scores turned into weights with softmax.",
        "card": "Type a phrase, pick a word, and see similarity scores turn into attention weights with softmax.",
        "title": "Attention Visualizer: How Transformer Attention Works",
        "description": "Type a phrase and see a simplified transformer attention map: word vectors, dot-product similarity and softmax weights. Free interactive NLP lab.",
        "track": "nlp",
        "videos": ["vd40uSemRrE", "FxMcnUEBBTs"],
    },
]

LAB_EXPLAINERS = {
    "regression": """
<h2>How gradient descent works</h2>
<p>The model is a polynomial: a curve described by a few weights. Training means finding the weights that make the curve pass as close as possible to your points.</p>
<h3>1. Measure the error</h3>
<p>For every point the model makes a prediction, and we measure how far off it is. Squaring those errors and averaging them gives the <strong>mean squared error</strong>: the loss shown in the panel.</p>
<h3>2. Step downhill</h3>
<p>The gradient says how the loss changes when each weight moves a little. Gradient descent moves every weight a small step against it: <code>w = w − learning_rate × gradient</code>. Repeat, and the loss falls.</p>
<h3>3. Pick the learning rate carefully</h3>
<p>Too small and training crawls. Too large and every step overshoots the minimum, so the loss explodes. Try the <strong>Exploding</strong> preset, then lower the rate.</p>
<h3>4. Match the model to the data</h3>
<p>A degree-1 model can only draw a straight line. Higher degrees can bend, but they can also start chasing noise. That trade-off is where overfitting begins.</p>
""",
    "boundary": """
<h2>How the three classifiers draw the line</h2>
<p>Every spot on the plane gets a predicted class, and the shading shows those predictions. The edge between the colours is the decision boundary.</p>
<h3>K-nearest neighbours</h3>
<p>KNN has no training step. To classify a spot it finds the K closest examples and takes a vote. A small K follows every point, outliers included. A larger K gives a smoother boundary.</p>
<h3>Logistic regression</h3>
<p>Logistic regression learns one weighted sum of the inputs and passes it through a sigmoid. Its boundary is always a straight line, which is why it fails on the <strong>XOR</strong> preset. The regularization slider pulls the weights toward zero.</p>
<h3>A small neural network</h3>
<p>The network adds a hidden layer of tanh units. Each unit draws its own line and the output combines them, so the boundary can bend around XOR. More hidden units give it more flexibility.</p>
<p>Train accuracy only tells you how well a model fits the points it has seen. A model that scores 100% here can still fail on new data.</p>
""",
    "clusters": """
<h2>How k-means finds clusters</h2>
<p>K-means is unsupervised: the points have no labels. It looks for K groups by repeating two steps until nothing changes.</p>
<h3>1. Assign</h3>
<p>Every point joins the cluster of its nearest centroid (the stars).</p>
<h3>2. Update</h3>
<p>Every centroid moves to the average position of the points assigned to it.</p>
<h3>Inertia</h3>
<p>Inertia is the average squared distance from each point to its centroid. Neither step can increase it, which is why k-means always settles. It can settle on a poor solution, so regenerate the data and compare.</p>
<h3>Where k-means struggles</h3>
<p>K-means assumes round, similar-sized clusters. Choose the <strong>Rings</strong> dataset: the two rings are obvious to you, but k-means cuts them into wedges.</p>
""",
    "attention": """
<h2>How this attention map works</h2>
<p>In a transformer, each word looks at the other words and decides how much attention to pay to each one. This lab shows the core of that idea with a simplified model.</p>
<h3>1. Words become vectors</h3>
<p>Each word becomes a small vector of numbers. Here the vectors come from the word's letters, which keeps the lab fast and predictable. Real models learn these embeddings from data.</p>
<h3>2. Similarity becomes a score</h3>
<p>The selected word (the query) is compared with every word using a dot product. Similar vectors get higher scores.</p>
<h3>3. Softmax turns scores into weights</h3>
<p>Softmax converts the scores into weights that add up to 100%. The sharpness slider scales the scores first: higher sharpness focuses attention on the best match, lower spreads it out.</p>
<p>Real transformers use separate learned query, key and value vectors and many attention heads, but the central step, similarity followed by softmax, is the same.</p>
""",
}

# Interactive lab markup. IDs are used by assets/js/playground.js.
LAB_PANELS = {
    "regression": """
<div class="lab-panel" id="panel-regression">
  <div class="lab-intro"><div><span class="eyebrow no-line">Lab 01 / Signature experiment</span><h2>Optimizer Step</h2><p>Add or drag points, then watch gradient descent learn the curve one step at a time.</p></div><span class="lab-chip">REGRESSION</span></div>
  <div class="lab-layout">
    <div class="lab-canvas-wrap"><canvas id="regressionCanvas" width="720" height="430" aria-label="Regression plot. Click or tap to add a point; drag points to move them."></canvas><p class="canvas-hint">Click to add a point · Drag to move one</p></div>
    <div class="lab-controls">
      <label>Learning rate <output id="lrValue">0.080</output><input id="learningRate" type="range" min="0.005" max="1.5" step="0.005" value="0.08"></label>
      <label>Polynomial degree <output id="degreeValue">2</output><input id="degree" type="range" min="1" max="4" step="1" value="2"></label>
      <div class="control-buttons"><button class="button button-primary" id="regRun" type="button">Pause training</button><button class="button button-outline" id="regReset" type="button">Reset</button></div>
      <div class="preset-row"><span>Try a preset</span><button data-reg-preset="linear" type="button">Linear</button><button data-reg-preset="curve" type="button">Curve</button><button data-reg-preset="explode" type="button">Exploding</button></div>
      <div class="metrics"><div><span>Loss</span><strong id="regLoss">—</strong></div><div><span>Steps</span><strong id="regSteps">0</strong></div></div>
      <p class="lab-insight" id="regInsight" aria-live="polite">Each step nudges the weights in the direction that reduces the loss.</p>
    </div>
  </div>
</div>""",
    "boundary": """
<div class="lab-panel" id="panel-boundary">
  <div class="lab-intro"><div><span class="eyebrow no-line">Lab 02 / Classification</span><h2>Decision Boundary Painter</h2><p>Paint examples of two classes and see where each classifier draws the line.</p></div><span class="lab-chip">CLASSIFICATION</span></div>
  <div class="lab-layout">
    <div class="lab-canvas-wrap"><canvas id="boundaryCanvas" width="720" height="430" aria-label="Classification plane. Click or tap to add a point of the selected class."></canvas><p class="canvas-hint">Pick a class · Click to paint</p></div>
    <div class="lab-controls">
      <label>Algorithm<select id="boundaryAlgorithm"><option value="knn">K-nearest neighbours</option><option value="logistic">Logistic regression</option><option value="neural">Small neural network</option></select></label>
      <div class="class-picker" role="group" aria-label="Paint class"><span>Paint class</span><button class="class-button" data-class="0" type="button" aria-pressed="true">● Indigo</button><button class="class-button" data-class="1" type="button" aria-pressed="false">● Coral</button></div>
      <label id="boundaryParamLabel">Neighbours (K) <output id="boundaryParamValue">5</output><input id="boundaryParam" type="range" min="1" max="15" step="2" value="5"></label>
      <div class="preset-row"><span>Try a preset</span><button data-boundary-preset="diagonal" type="button">Diagonal</button><button data-boundary-preset="xor" type="button">XOR</button><button data-boundary-preset="clear" type="button">Clear</button></div>
      <div class="metrics"><div><span>Points</span><strong id="boundaryPoints">0</strong></div><div><span>Train accuracy</span><strong id="boundaryAccuracy">—</strong></div></div>
      <p class="lab-insight" id="boundaryInsight" aria-live="polite">KNN votes with the nearest examples.</p>
    </div>
  </div>
</div>""",
    "clusters": """
<div class="lab-panel" id="panel-clusters">
  <div class="lab-intro"><div><span class="eyebrow no-line">Lab 03 / Unsupervised learning</span><h2>K-Means Sandbox</h2><p>Watch centroids move as the algorithm groups unlabelled data.</p></div><span class="lab-chip">CLUSTERING</span></div>
  <div class="lab-layout">
    <div class="lab-canvas-wrap"><canvas id="clusterCanvas" width="720" height="430" aria-label="K-means plot showing data points and centroids."></canvas><p class="canvas-hint">Stars are centroids · Colours show clusters</p></div>
    <div class="lab-controls">
      <label>Number of clusters (K) <output id="clusterKValue">3</output><input id="clusterK" type="range" min="2" max="6" step="1" value="3"></label>
      <label>Dataset<select id="clusterDataset"><option value="blobs">Blobs</option><option value="rings">Rings</option><option value="random">Random</option></select></label>
      <div class="control-buttons"><button class="button button-primary" id="clusterStep" type="button">Step once</button><button class="button button-outline" id="clusterAuto" type="button">Auto-run</button></div>
      <button class="quiet-button" id="clusterReset" type="button">Regenerate dataset</button>
      <div class="metrics"><div><span>Iteration</span><strong id="clusterIteration">0</strong></div><div><span>Inertia</span><strong id="clusterInertia">—</strong></div></div>
      <p class="lab-insight" id="clusterInsight" aria-live="polite">Each step assigns points to the nearest centroid, then moves each centroid to the middle of its group.</p>
    </div>
  </div>
</div>""",
    "attention": """
<div class="lab-panel" id="panel-attention">
  <div class="lab-intro"><div><span class="eyebrow no-line">Lab 04 / Language models</span><h2>Text Attention Explorer</h2><p>Type a short phrase, choose a word, and inspect a simplified similarity-based attention map.</p></div><span class="lab-chip">NLP</span></div>
  <div class="attention-layout">
    <div class="attention-main">
      <label class="phrase-label">Your phrase<input id="attentionText" type="text" value="the curious robot learns from data" maxlength="80" autocomplete="off"></label>
      <div class="token-list" id="tokenList" role="group" aria-label="Words in your phrase. Choose one as the query."></div>
      <div class="attention-bars" id="attentionBars" aria-live="polite"></div>
    </div>
    <div class="lab-controls">
      <label>Attention sharpness <output id="attentionSharpnessValue">3</output><input id="attentionSharpness" type="range" min="1" max="10" value="3"></label>
      <div class="preset-row"><span>Try a preset</span><button data-attention-preset="robot" type="button">Robot</button><button data-attention-preset="animals" type="button">Animals</button><button data-attention-preset="code" type="button">Code</button></div>
      <div class="metrics"><div><span>Tokens</span><strong id="attentionCount">6</strong></div><div><span>Top match</span><strong id="attentionTop">—</strong></div></div>
      <p class="lab-insight">This is a teaching model: deterministic word features and softmax, not a pretrained transformer.</p>
    </div>
  </div>
</div>""",
}

FAQS = [
    ("Is it really free?",
     "Yes. The first 100 students who claim a founding seat get all four launch tracks free. You don't enter any payment details. The planned regular price is {planned_price}."),
    ("When do the courses start?",
     "The tracks open in stages. Founding students get the start date for their track by email before it opens. Until then you can use the free ML Playground and the YouTube lessons."),
    ("Do I need to know Python already?",
     "No. ML Foundations starts with the core ideas and guided Python examples. Basic coding familiarity helps, but you can begin as a curious beginner."),
    ("What will I build?",
     "Every track ends with a project: a model that predicts a real-world outcome, a PyTorch image classifier, a text classifier you can inspect, and a grounded question-answering system built with RAG."),
    ("What happens when the 100 seats are gone?",
     "You can still sign up. ML Foundations stays free for everyone, and you'll join the waitlist in case more founding seats open."),
    ("Is the seat counter real?",
     "Yes. It counts confirmed founding signups and updates as people join. The \"seat claimed\" notices are real signups too: they show the seat number, track, experience level and roughly when, never a name."),
    ("How do you use my details?",
     "Only to manage your seat and email you about the courses. We never sell your data, and you can ask us to delete it at any time. The <a href=\"/privacy/\">privacy policy</a> has the details."),
    ("Does the ML Playground use an AI API?",
     "No. The labs run entirely in your browser with JavaScript and Canvas. There's no API key, account or backend involved."),
]

# ---------------------------------------------------------------------------
# Price ladder (planned prices: the paid tiers open with the tracks).
# A free entry course brings people into Optimizer Step; each paid tier then costs a little
# more than the one below for a clearly bigger result (good / better / best), with a premium
# Pro tier at the top as the anchor. "Pay only the difference" makes every step up small.
# Prices come from the market research in notes/pricing-research-2026-11-20.md.
# Founding students get All Tracks free and keep FOUNDING_DISCOUNT % off upgrades.
# Every promise here is published on the site: keep it deliverable.
FOUNDING_DISCOUNT = 40
PRO_LIVE_MONTHS = 12
PRICE_TIERS = [
    {
        "id": "starter",
        "name": "Starter",
        "price": 0,
        "tagline": "Your way into Optimizer Step. Free, for good.",
        "includes": [
            "ML Foundations: the complete beginner track",
            "Its project: predict a real-world outcome",
            "The ML Playground and every free YouTube lesson",
        ],
    },
    {
        "id": "track",
        "name": "Single Track",
        "price": 999,
        "tagline": "Go deep on the one skill you need.",
        "includes": [
            "Everything in Starter",
            "One advanced track of your choice: Deep Learning & Vision, NLP & Transformers or Build with RAG",
            "That track's project",
            "A certificate for each track you complete",
        ],
    },
    {
        "id": "all",
        "name": "All Tracks",
        "price": 1999,
        "badge": "Best value",
        "tagline": "The whole path, from regression to RAG.",
        "includes": [
            "Everything in Starter",
            "All three advanced tracks",
            "All four projects for your portfolio",
            "A certificate for each track you complete",
        ],
    },
    {
        "id": "pro",
        "name": "Pro",
        "price": 4999,
        "tagline": "All Tracks, plus live help and feedback on your projects.",
        "includes": [
            "Everything in All Tracks",
            "A live Q&A every month for 12 months",
            "Written feedback on each of your track projects",
            "A certificate for each track you complete",
        ],
    },
]

# Every price the site prints comes from PRICE_TIERS, so the pages can never disagree.
# The founding offer gives All Tracks free, so its planned price is the All Tracks price.
_PRICE = {t["id"]: t["price"] for t in PRICE_TIERS}
SITE["planned_price_number"] = _PRICE["all"]
SITE["planned_price"] = f"₹{_PRICE['all']:,}"
SITE["price_track"] = f"₹{_PRICE['track']:,}"
SITE["price_all"] = f"₹{_PRICE['all']:,}"
SITE["price_pro"] = f"₹{_PRICE['pro']:,}"
SITE["founding_discount"] = FOUNDING_DISCOUNT

FAQS[0] = ("Is it really free?",
           "Yes. The first 100 students who claim a founding seat get all four launch tracks free: the All Tracks tier, "
           "which costs {planned_price} after the founding cohort. You don't enter any payment details. After the founding cohort, ML Foundations "
           "stays free for everyone and the other tracks are paid. See <a href=\"/pricing/\">pricing</a>.")
FAQS.insert(1, ("What will the paid tracks cost?",
                "ML Foundations is free for everyone. After that it's {price_track} for one advanced track, {price_all} for "
                "All Tracks, or {price_pro} for Pro, which adds a monthly live Q&A and written feedback on your projects. "
                "These are one-time prices that include all taxes, and you can upgrade any time by paying only the difference. "
                "Founding students keep {founding_discount}% off every upgrade."))

# ---------------------------------------------------------------------------
# "What AI teams hire for" (home page). Skills named in current technical AI / machine-learning
# job posts on each company's own careers site, checked on SKILLS_CHECKED. Every company listed
# under a skill has at least one such post (the example in "sources"); the full evidence is in
# notes/skills-evidence-2026-11-20.json. Company NAMES only, never logos: they describe public
# job posts, and Optimizer Step is not affiliated with or endorsed by these companies.
# Re-check the posts before changing SKILLS_CHECKED.
SKILLS_CHECKED = '20 November 2026'
SKILLS_POSTS_READ = 'about 880'
SKILL_COMPANIES = ['OpenAI',
 'Google',
 'Anthropic',
 'Microsoft',
 'Meta',
 'Amazon',
 'Databricks',
 'Hugging Face',
 'Sarvam AI',
 'Perplexity',
 'Swiggy',
 'PhonePe',
 'Meesho']
SKILL_DEMAND = [{'track': 'foundations',
  'title': 'Python and ML fundamentals',
  'text': 'Writing Python, working with data, and knowing how a model learns and how to judge it honestly.',
  'companies': ['OpenAI', 'Google', 'Microsoft', 'Anthropic', 'Amazon', 'Sarvam AI', 'PhonePe', 'Meesho'],
  'sources': [('OpenAI',
               'Training: ML Framework Engineer',
               'https://jobs.ashbyhq.com/openai/d8794980-1d3f-4d82-8b48-811449b6c492'),
              ('Google',
               'Software Engineer, AI/ML, GeminiApp, DeepMind',
               'https://www.google.com/about/careers/applications/jobs/results/75356771341738694-software-engineer-aiml-geminiapp-deepmind'),
              ('Microsoft',
               'Data Scientist 2',
               'https://apply.careers.microsoft.com/careers/job/1970393557074752'),
              ('Anthropic',
               'Applied AI Engineer, Commercial',
               'https://job-boards.greenhouse.io/anthropic/jobs/5483945008'),
              ('Amazon',
               'Applied Scientist II, Detail Page',
               'https://www.amazon.jobs/en/jobs/10602090/applied-scientist-ii-detail-page'),
              ('Sarvam AI',
               'Data Scientist - Evaluations, Chanakya',
               'https://jobs.ashbyhq.com/sarvam/7c42207a-bb56-413c-839f-9ad692df840e'),
              ('PhonePe',
               'Data Scientist (3-5 years)',
               'https://jobs.smartrecruiters.com/PHONEPELIMITED/1000000000003993-data-scientist-3-5-years-'),
              ('Meesho',
               'Data Scientist III',
               'https://jobs.lever.co/meesho/489fe662-5d28-4305-953e-91ee21e8538c')]},
 {'track': 'deep-learning',
  'title': 'PyTorch and deep learning',
  'text': 'Neural networks, backpropagation and computer vision, built and debugged in PyTorch.',
  'companies': ['Google', 'Meta', 'Microsoft', 'OpenAI', 'Amazon', 'Hugging Face', 'Sarvam AI', 'PhonePe'],
  'sources': [('Google',
               'Post-Doctoral Researcher, PhD, DeepMind, 2026 Start (Fixed-Term Contract)',
               'https://www.google.com/about/careers/applications/jobs/results/129129141264884422-postdoctoral-researcher-phd-deepmind-2026-start-fixedterm-contract'),
              ('Meta',
               'Machine Learning Engineer (Technical Leadership)',
               'https://www.metacareers.com/profile/job_details/1619290696213069/'),
              ('Microsoft',
               'Data Scientist 2',
               'https://apply.careers.microsoft.com/careers/job/1970393557074752'),
              ('OpenAI',
               'Research Engineer',
               'https://jobs.ashbyhq.com/openai/240d459b-696d-43eb-8497-fab3e56ecd9b'),
              ('Amazon',
               'Sr Applied Scientist, Amazon Shipping',
               'https://www.amazon.jobs/en/jobs/10592212/sr-applied-scientist-amazon-shipping'),
              ('Hugging Face',
               'Open-Source Machine Learning Engineer - US Remote',
               'https://apply.workable.com/huggingface/j/19A136F8E2/'),
              ('Sarvam AI',
               'ML Engineer (Training Infra), Foundational Models',
               'https://jobs.ashbyhq.com/sarvam/e9fb1269-fc4b-4879-aa35-0b75a8c83611'),
              ('PhonePe',
               'Data Scientist (3-5 years)',
               'https://jobs.smartrecruiters.com/PHONEPELIMITED/1000000000003993-data-scientist-3-5-years-')]},
 {'track': 'nlp',
  'title': 'LLMs, transformers and NLP',
  'text': 'Tokens, embeddings and attention: the ideas inside every large language model.',
  'companies': ['Google', 'Microsoft', 'Meta', 'Anthropic', 'OpenAI', 'Amazon', 'Sarvam AI', 'Swiggy'],
  'sources': [('Google',
               'Software Engineer, AI/ML, GeminiApp, DeepMind',
               'https://www.google.com/about/careers/applications/jobs/results/75356771341738694-software-engineer-aiml-geminiapp-deepmind'),
              ('Microsoft',
               'Data Scientist 2',
               'https://apply.careers.microsoft.com/careers/job/1970393557074752'),
              ('Meta',
               'Applied AI Architect, Meta Enterprise Platform (India)',
               'https://www.metacareers.com/profile/job_details/2543470749484713/'),
              ('Anthropic',
               'Applied AI Engineer, Beneficial Deployments (Clinical Development, Rare and Neglected '
               'Diseases)',
               'https://job-boards.greenhouse.io/anthropic/jobs/5445760008'),
              ('OpenAI',
               'Researcher, Safety Training',
               'https://jobs.ashbyhq.com/openai/2560ed50-5535-42b8-b069-9ebc28ce7493'),
              ('Amazon',
               'Applied Scientist II, Detail Page',
               'https://www.amazon.jobs/en/jobs/10602090/applied-scientist-ii-detail-page'),
              ('Sarvam AI',
               'Data Scientist - Evaluations, Chanakya',
               'https://jobs.ashbyhq.com/sarvam/7c42207a-bb56-413c-839f-9ad692df840e'),
              ('Swiggy',
               'Senior Manager - Applied Science',
               'https://jobs.smartrecruiters.com/SWIGGY/6000000001491426-senior-manager-applied-science')]},
 {'track': 'rag',
  'title': 'RAG, embeddings and vector search',
  'text': 'Connecting language models to your own data with retrieval, vector search and careful evaluation.',
  'companies': ['Google', 'Microsoft', 'Meta', 'OpenAI', 'Amazon', 'Databricks', 'Perplexity', 'Sarvam AI'],
  'sources': [('Google',
               'Forward Deployed Engineer V, GenAI, Google Cloud',
               'https://www.google.com/about/careers/applications/jobs/results/85646978259526342-forward-deployed-engineer-v-genai-google-cloud'),
              ('Microsoft',
               'Principal Applied Scientist- Foundation Models, Agents & Decision Intelligence',
               'https://apply.careers.microsoft.com/careers/job/1970393556942186'),
              ('Meta',
               'Applied AI Architect, Meta Enterprise Platform (India)',
               'https://www.metacareers.com/profile/job_details/2543470749484713/'),
              ('OpenAI',
               'Research Scientist / Research Engineer - Foundations, Search',
               'https://jobs.ashbyhq.com/openai/020b2aae-8be0-408c-ab49-20eefa8541af'),
              ('Amazon',
               'Data Scientist II, AWS - Quick',
               'https://www.amazon.jobs/en/jobs/10602065/data-scientist-ii-aws-quick'),
              ('Databricks',
               'AI Automation Engineer',
               'https://databricks.com/company/careers/open-positions/job?gh_jid=8829033002'),
              ('Perplexity',
               'Member of Technical Staff (Machine Learning Engineer, Search)',
               'https://jobs.ashbyhq.com/Perplexity/0190699f-010b-44f2-8399-278899fef018'),
              ('Sarvam AI',
               'Embedded Data Scientist, Chanakya',
               'https://jobs.ashbyhq.com/sarvam/dc047f4f-97be-4bb3-a9f1-cebbfc4de3e6')]}]
