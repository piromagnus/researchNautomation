import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:url_launcher/url_launcher.dart';

import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:firebase_core/firebase_core.dart';

import 'firebase_options.dart'; // This file will be created in the next step


/// A Flutter app that displays AI paper abstracts in a TikTok-style vertical feed
/// using an ethereal, pastel theme and more diverse widgets.
/// Now includes a Firebase model for storing papers.
void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  await Firebase.initializeApp(

    options: DefaultFirebaseOptions.currentPlatform,

  );

  runApp(const MyApp());
}

/// Model class representing a paper.
class PaperModel {
  final String id;
  final String title;
  final String summary;
  final String link;
  final DateTime? createdAt;
  final bool like;

  PaperModel({
    required this.id,
    required this.title,
    required this.summary,
    required this.link,
    required this.like,
    this.createdAt,
  });

  // Convert a Firestore DocumentSnapshot into a PaperModel.
  factory PaperModel.fromDocument(DocumentSnapshot doc) {
    final data = doc.data() as Map<String, dynamic>? ?? {};
    return PaperModel(
      id: doc.id,
      title: data['title'] ?? '',
      summary: data['summary'] ?? '',
      link: data['link'] ?? '',
      createdAt: (data['timestamp'] as Timestamp?)?.toDate(),
      like: data['like'] ?? false,
    );
  }

  /// Convert PaperModel to a map for saving to Firestore.
  Map<String, dynamic> toMap() {
    return {
      'title': title,
      'summary': summary,
      'link': link,
      // Use FieldValue.serverTimestamp() for creation time if needed.
      'timestamp': FieldValue.serverTimestamp(),
      'like': like,
    };
  }
}

/// Repository to manage Firestore interactions for papers.
class PaperRepository {
  final FirebaseFirestore _firestore = FirebaseFirestore.instance;
  final int _batchSize = 10;

  /// Add a new paper to the 'papers' collection.
  Future<void> addPaper(PaperModel paper) async {
    await _firestore.collection('papers').add(paper.toMap());
  }

  /// Update paper's like status
  Future<void> updateLike(String paperId, bool like) async {
    await _firestore.collection('papers').doc(paperId).update({'like': like});
  }

  /// Retrieve paginated papers from Firestore.
  Future<List<PaperModel>> getPaginatedPapers(DocumentSnapshot? lastDocument) async {
    var query = _firestore.collection('papers')
        .orderBy('timestamp', descending: true)
        .limit(_batchSize);

    if (lastDocument != null) {
      query = query.startAfterDocument(lastDocument);
    }

    final querySnapshot = await query.get();
    return querySnapshot.docs.map((doc) => PaperModel.fromDocument(doc)).toList();
  }
}

class MyApp extends StatelessWidget {
  const MyApp({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'TikTok-like AI Papers',
      theme: ThemeData(
        useMaterial3: true,
        brightness: Brightness.dark,
        scaffoldBackgroundColor: const Color(0xFF0A1929),
        colorScheme: ColorScheme.dark(
          primary: const Color(0xFF64FFDA),     // Cyan éthéré
          secondary: const Color(0xFF7B5BF2),   // Violet électrique
          surface: const Color(0xFF0A1929),     // Bleu nuit profond
          background: const Color(0xFF132F4C),  // Bleu profond inversé
          tertiary: const Color(0xFF4CC9F0),    // Cyan électrique
        ),
        textTheme: const TextTheme(
          titleLarge: TextStyle(
            fontSize: 24,
            fontWeight: FontWeight.w600,
            color: Color(0xFFE6FFF9),
            letterSpacing: 0.5,
          ),
          bodyMedium: TextStyle(
            fontSize: 16,
            color: Color(0xFFB8E6FF),
            letterSpacing: 0.3,
          ),
          bodySmall: TextStyle(
            fontSize: 14,
            color: Color(0xFF64FFDA),
            letterSpacing: 0.4,
          ),
        ),
        cardTheme: CardTheme(
          elevation: 8,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(20.0),
          ),
        ),
      ),
      home: const ArxivFeedPage(),
    );
  }
}

class PaperEntry {
  final String title;
  final String summary;
  final String link;

  PaperEntry({required this.title, required this.summary, required this.link});
}

class ArxivFeedPage extends StatefulWidget {
  const ArxivFeedPage({Key? key}) : super(key: key);

  @override
  State<ArxivFeedPage> createState() => _ArxivFeedPageState();
}

class _ArxivFeedPageState extends State<ArxivFeedPage> {
  final PageController _pageController = PageController(viewportFraction: 1.0);
  final PaperRepository _repository = PaperRepository();
  List<PaperModel> _papers = [];
  bool _isLoading = false;
  DocumentSnapshot? _lastDocument;
  int _currentPage = 0;

  @override
  void initState() {
    super.initState();
    _loadMorePapers();
    _pageController.addListener(_onScroll);
  }

  void _onScroll() {
    if (_pageController.position.pixels == _pageController.position.maxScrollExtent) {
      _loadMorePapers();
    }
  }

  Future<void> _loadMorePapers() async {
    if (_isLoading) return;

    setState(() {
      _isLoading = true;
    });

    try {
      final papers = await _repository.getPaginatedPapers(_lastDocument);
      
      if (papers.isEmpty) {
        // If no more papers in Firebase, fetch from arXiv
        await _fetchFromArxiv();
      } else {
        setState(() {
          _papers.addAll(papers);
          _lastDocument = papers.last as DocumentSnapshot;
          _isLoading = false;
        });
      }
    } catch (e) {
      setState(() {
        _isLoading = false;
      });
    }
  }

  Future<void> _fetchFromArxiv() async {
    try {
      final url = Uri.parse('http://export.arxiv.org/api/query?search_query=cat:cs.CV&sortBy=submittedDate&sortOrder=descending&max_results=10');
      final response = await http.get(url);
      
      if (response.statusCode == 200) {
        final entries = _extractEntries(response.body);
        
        // Save to Firebase and add to current list
        for (var entry in entries) {
          final paper = PaperModel(
            id: '',
            title: entry.title,
            summary: entry.summary,
            link: entry.link,
            like: false,
          );
          await _repository.addPaper(paper);
        }
        
        // Reload papers from Firebase
        final newPapers = await _repository.getPaginatedPapers(_lastDocument);
        setState(() {
          _papers.addAll(newPapers);
          if (newPapers.isNotEmpty) {
            _lastDocument = newPapers.last as DocumentSnapshot;
          }
          _isLoading = false;
        });
      }
    } catch (_) {
      setState(() {
        _isLoading = false;
      });
    }
  }

  Future<void> _toggleLike(PaperModel paper) async {
    if (paper.id.isEmpty) return;
    
    await _repository.updateLike(paper.id, !paper.like);
    setState(() {
      final index = _papers.indexWhere((p) => p.id == paper.id);
      if (index != -1) {
        _papers[index] = PaperModel(
          id: paper.id,
          title: paper.title,
          summary: paper.summary,
          link: paper.link,
          like: !paper.like,
          createdAt: paper.createdAt,
        );
      }
    });
  }

  List<PaperEntry> _extractEntries(String feed) {
    final List<PaperEntry> results = [];
    final pattern = RegExp(
      r'<entry>.*?<title>(.*?)</title>.*?<summary>(.*?)</summary>.*?<id>(.*?)</id>.*?</entry>',
      dotAll: true,
    );

    for (final match in pattern.allMatches(feed)) {
      final title = match.group(1)?.trim() ?? '';
      final summary = match.group(2)?.trim() ?? '';
      final link = match.group(3)?.trim() ?? '';
      results.add(PaperEntry(title: title, summary: summary, link: link));
    }
    return results;
  }

  Future<void> _launchURL(String urlString) async {
    final Uri url = Uri.parse(urlString);
    if (!await launchUrl(url, mode: LaunchMode.externalApplication)) {
      throw Exception('Could not launch $url');
    }
  }

  void _showDetails(BuildContext context, PaperEntry paper) {
    Navigator.of(context).push(
      MaterialPageRoute(
        builder: (ctx) => Scaffold(
          backgroundColor: Theme.of(context).colorScheme.surface,
          appBar: AppBar(
            title: const Text('Paper Details'),
            backgroundColor: Theme.of(context).colorScheme.surface,
            elevation: 0,
          ),
          body: Padding(
            padding: const EdgeInsets.all(16.0),
            child: SingleChildScrollView(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    paper.title,
                    style: Theme.of(context).textTheme.titleLarge,
                  ),
                  const SizedBox(height: 12),
                  Text(
                    paper.summary,
                    style: Theme.of(context).textTheme.bodyMedium,
                  ),
                  const SizedBox(height: 20),
                  GestureDetector(
                    onTap: () => _launchURL(paper.link),
                    child: Container(
                      padding: const EdgeInsets.symmetric(vertical: 8, horizontal: 12),
                      decoration: BoxDecoration(
                        borderRadius: BorderRadius.circular(8),
                        border: Border.all(
                          color: Theme.of(context).colorScheme.primary.withAlpha(77),
                        ),
                      ),
                      child: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Icon(
                            Icons.launch,
                            size: 16,
                            color: Theme.of(context).colorScheme.primary,
                          ),
                          const SizedBox(width: 8),
                          Text(
                            'View on arXiv',
                            style: Theme.of(context).textTheme.bodySmall?.copyWith(
                              color: Theme.of(context).colorScheme.primary,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Ethereal AI Papers'),
        elevation: 0,
        backgroundColor: Theme.of(context).colorScheme.surface,
      ),
      body: PageView.builder(
        controller: _pageController,
        scrollDirection: Axis.vertical,
        itemCount: _papers.length + (_isLoading ? 1 : 0),
        itemBuilder: (context, index) {
          if (index >= _papers.length) {
            return const Center(child: CircularProgressIndicator());
          }

          final paper = _papers[index];
          return GestureDetector(
            onTap: () {
              _showDetails(context, PaperEntry(
                title: paper.title,
                summary: paper.summary,
                link: paper.link
              ));
            },
            child: Stack(
              children: [
                Container(
                  decoration: BoxDecoration(
                    gradient: LinearGradient(
                      colors: [
                        Theme.of(context).colorScheme.surface,
                        Theme.of(context).colorScheme.secondary.withAlpha(75),
                      ],
                      begin: Alignment.topCenter,
                      end: Alignment.bottomCenter,
                    ),
                  ),
                  child: Center(
                    child: Padding(
                      padding: const EdgeInsets.all(24.0),
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        crossAxisAlignment: CrossAxisAlignment.center,
                        children: [
                          _PaperTitle(title: paper.title),
                          const SizedBox(height: 12),
                          _PaperSummary(summary: paper.summary),
                          const SizedBox(height: 16),
                          _PaperIconDecoration(index: index),
                        ],
                      ),
                    ),
                  ),
                ),
                Positioned(
                  right: 16,
                  bottom: 16,
                  child: IconButton(
                    icon: Icon(
                      paper.like ? Icons.favorite : Icons.favorite_border,
                      color: Theme.of(context).colorScheme.primary,
                    ),
                    onPressed: () => _toggleLike(paper),
                  ),
                ),
              ],
            ),
          );
        },
      ),
    );
  }
  
  @override
  void dispose() {
    _pageController.removeListener(_onScroll);
    _pageController.dispose();
    super.dispose();
  }
}

class _PaperTitle extends StatelessWidget {
  final String title;

  const _PaperTitle({Key? key, required this.title}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16.0, vertical: 12.0),
      decoration: BoxDecoration(
        color: Theme.of(context).colorScheme.surface.withAlpha(204), // 0.8 -> 204
        borderRadius: BorderRadius.circular(20.0),
        border: Border.all(
          color: Theme.of(context).colorScheme.primary.withAlpha(77), // 0.3 -> 77
          width: 1,
        ),
        boxShadow: [
          BoxShadow(
            color: Theme.of(context).colorScheme.primary.withAlpha(51), // 0.2 -> 51
            blurRadius: 12,
            spreadRadius: 2,
          ),
        ],
      ),
      child: Text(
        title,
        style: Theme.of(context).textTheme.titleLarge,
        textAlign: TextAlign.center,
      ),
    );
  }
}

class _PaperSummary extends StatelessWidget {
  final String summary;

  const _PaperSummary({Key? key, required this.summary}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Card(
      elevation: 4,
      color: Theme.of(context).colorScheme.surface.withAlpha(179), // 0.7 -> 179
      child: Container(
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(16.0),
          border: Border.all(
            color: Theme.of(context).colorScheme.secondary.withAlpha(51), // 0.2 -> 51
            width: 1,
          ),
        ),
        child: Padding(
          padding: const EdgeInsets.all(16.0),
          child: Text(
            summary,
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
              height: 1.5,
            ),
            maxLines: 6,
            overflow: TextOverflow.ellipsis,
            textAlign: TextAlign.center,
          ),
        ),
      ),
    );
  }
}

class _PaperIconDecoration extends StatelessWidget {
  final int index;
  const _PaperIconDecoration({Key? key, required this.index}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    final icons = [
      Icons.science_outlined,
      Icons.psychology_outlined,
      Icons.biotech_outlined,
      Icons.memory_outlined,
      Icons.precision_manufacturing_outlined,
    ];
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        shape: BoxShape.circle,
        color: Theme.of(context).colorScheme.surface.withAlpha(77), // 0.3 -> 77
        border: Border.all(
          color: Theme.of(context).colorScheme.primary.withAlpha(77), // 0.3 -> 77
          width: 1,
        ),
      ),
      child: Icon(
        icons[index % icons.length],
        size: 32,
        color: Theme.of(context).colorScheme.primary,
      ),
    );
  }
}
